import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from trading_65 import (apply, fresh_state, read_state, write_state, summary, snapshot)

P = {f'{i:02d}': {'character_id': f'{i:02d}', 'identity_extension': {'姓名': f'成员{i}', '居住城市':'布加勒斯特'}, 'source_profile': {'性别': '男','年龄':45,'学员资历':'新男','工作_职业':'测试'}} for i in range(1,66)}

class Trading65Tests(unittest.TestCase):
    def setUp(self):
        self.s=fresh_state()
        self.day='2026-10-10'
        for pid in ['01','02']:
            apply(self.s,P,'eligibility',{'person_id':pid,'opened':True,'currency':'RON','funds':1000,'frequency':'HIGH','required_today':pid=='01'})
        self.o=apply(self.s,P,'create_offer',{'symbol':'TEST','name':'教学测试','market':'BVB','currency':'RON','unit_price':10,'min_shares':5,'hold_days':2,'participant_count':3,'discount_pct':0})
    def rec(self):return apply(self.s,P,'recommend',{'offer_id':self.o['id'],'date':self.day})
    def invite(self):self.rec();return apply(self.s,P,'invite',{'offer_id':self.o['id'],'person_id':'01','date':self.day})
    def buy(self):self.invite();return apply(self.s,P,'buy',{'offer_id':self.o['id'],'person_id':'01','quantity':5,'date':self.day})
    def test_authoritative_65(self):self.assertEqual(summary(self.s,P)['metrics']['people'],65)
    def test_old_roster_rejected(self):
        with self.assertRaises(ValueError):apply(self.s,{**P,'70':P['01']},'recommend',{'offer_id':self.o['id']})
    def test_only_explicit_accounts_eligible(self):self.assertEqual([x['person_id'] for x in self.rec()['candidates']],['01','02'])
    def test_recommend_idempotent(self):
        r=self.rec();self.invite();self.assertEqual(self.rec()['id'],r['id']);self.assertEqual(self.rec()['candidates'][0]['status'],'invited')
    def test_reject_removes_pending_buy(self):
        self.invite();apply(self.s,P,'reject',{'offer_id':self.o['id'],'person_id':'01','date':self.day});self.assertEqual(len(self.s['buy_plans']),0)
    def test_buy_creates_holding_and_transaction(self):
        x=self.buy();self.assertEqual(x['holding']['person_id'],'01');self.assertEqual(self.s['transactions'][0]['type'],'buy')
    def test_buy_without_invite_denied(self):
        self.rec()
        with self.assertRaises(ValueError):apply(self.s,P,'buy',{'offer_id':self.o['id'],'person_id':'01','quantity':5,'date':self.day})
    def test_below_min_quantity_denied(self):
        self.invite()
        with self.assertRaises(ValueError):apply(self.s,P,'buy',{'offer_id':self.o['id'],'person_id':'01','quantity':4,'date':self.day})
    def test_over_budget_denied(self):
        self.invite()
        with self.assertRaises(ValueError):apply(self.s,P,'buy',{'offer_id':self.o['id'],'person_id':'01','quantity':150,'date':self.day})
    def test_duplicate_purchase_denied(self):
        self.buy()
        with self.assertRaises(ValueError):apply(self.s,P,'buy',{'offer_id':self.o['id'],'person_id':'01','quantity':5,'date':self.day})
    def test_immediate_sell_without_countdown(self):
        h=self.buy()['holding']
        self.assertNotIn('planned_sell_at', h)
        x=apply(self.s,P,'sell',{'holding_id':h['id'],'sell_price':12})
        self.assertEqual(x['transaction']['type'],'sell')
        self.assertEqual(h['status'],'sold')
        self.assertEqual(summary(self.s,P)['people'][0]['available_funds']['RON'],1010)
    def test_old_holdings_ignore_legacy_sell_lock(self):
        h=self.buy()['holding'];h['planned_sell_at']=(datetime.now(timezone.utc)+timedelta(days=999)).isoformat()
        apply(self.s,P,'sell',{'holding_id':h['id'],'sell_price':12})
        self.assertEqual(h['status'],'sold')
    def test_batch_buy_funds_percentage_and_cash_accounting(self):
        self.rec()
        res=apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':25,'person_ids':['01','02']})
        self.assertEqual(res['count'],2)
        self.assertEqual([r['quantity'] for r in res['purchased']],[25,25])
        self.assertEqual(summary(self.s,P)['people'][0]['available_funds']['RON'],750)
        self.assertEqual(self.s['revision'],5)  # setup eligibility*2, offer, recommend, batch
        self.assertEqual(len(self.s['transactions']),2)
        with self.assertRaises(ValueError):apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':25,'person_ids':['01','02']})
        self.assertEqual(len(self.s['transactions']),2)
    def test_batch_buy_fail_atomic_if_second_member_insufficient(self):
        self.rec()
        apply(self.s,P,'eligibility',{'person_id':'02','opened':True,'currency':'RON','funds':30})
        previous=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':25,'person_ids':['01','02']})
        self.assertEqual(self.s,previous)
    def test_batch_sell_and_realized_profit(self):
        self.rec()
        apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':20,'person_ids':['01','02']})
        hids=[h['id'] for h in self.s['holdings']]
        result=apply(self.s,P,'batch_sell',{'offer_id':self.o['id'],'holding_ids':hids,'sell_price':12})
        self.assertEqual(result['count'],2)
        self.assertEqual([p['available_funds']['RON'] for p in summary(self.s,P)['people'][:2]],[1040,1040])
        self.assertEqual(len(self.s['transactions']),4)
        with self.assertRaises(ValueError):apply(self.s,P,'sell',{'holding_id':hids[0],'sell_price':12})
    def test_batch_sell_failure_rollback(self):
        self.rec()
        apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':20,'person_ids':['01','02']})
        previous=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):apply(self.s,P,'batch_sell',{'offer_id':self.o['id'],'holding_ids':[self.s['holdings'][0]['id'],'invalid'],'sell_price':12})
        self.assertEqual(self.s,previous)
    def test_percentage_fraction_and_minimum(self):
        self.rec()
        res=apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':19.9,'person_ids':['01']})
        self.assertEqual(res['purchased'][0]['quantity'],19)
        self.assertAlmostEqual(summary(self.s,P)['people'][0]['available_funds']['RON'],810)
        with self.assertRaises(ValueError):apply(self.s,P,'batch_buy',{'offer_id':self.o['id'],'date':self.day,'allocation_pct':0,'person_ids':['02']})
    def test_snapshot_read_only(self):
        self.buy();before=copy.deepcopy(self.s);shot=snapshot(self.s,self.day,self.o['id']);self.assertGreater(len(shot['facts']),0);self.assertEqual(self.s,before)
    def test_atomic_read_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trades.json';write_state(p,self.s);self.assertEqual(read_state(p),self.s)
    def test_unknown_funds_ineligible(self):
        apply(self.s,P,'eligibility',{'person_id':'03','opened':True,'currency':'RON','funds':''});self.assertNotIn('03',[c['person_id'] for c in self.rec()['candidates']])
    def test_unknown_person_denied(self):
        with self.assertRaises(ValueError):apply(self.s,P,'eligibility',{'person_id':'70','opened':True})

if __name__=='__main__':unittest.main()