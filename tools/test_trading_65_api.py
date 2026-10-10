"""Simulated trade routes must accept only explicit operations and authenticated 65-person data."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import finance_skill_api as api

P = {f'{i:02d}': {'character_id': f'{i:02d}',
    'identity_extension': {'姓名': f'测试角色{i}', '居住城市':'布加勒斯特'},
    'source_profile': {'性别':'男','年龄':45,'学员资历':'新男','工作_职业':'测试'}}
    for i in range(1,66)}


class TradingAPIIntegration(unittest.TestCase):
    def test_end_to_end_without_implicit_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(api, 'load_profiles', return_value=P):
                with ThreadingHTTPServer(('127.0.0.1', 0), api.make_handler(Path(folder))) as server:
                    thread=threading.Thread(target=server.serve_forever,daemon=True)
                    thread.start()
                    base=f'http://127.0.0.1:{server.server_port}'
                    def get(url):
                        with urlopen(base+url) as res:return json.load(res)
                    def post(action, **payload):
                        data=json.dumps({'action':action, **payload}).encode('utf-8')
                        req=Request(base+'/api/trading/sim/action',data=data,
                                    method='POST',headers={'Content-Type':'application/json'})
                        with urlopen(req) as res:return json.load(res)
                    try:
                        with urlopen(base+'/trading') as r:
                            html=r.read().decode('utf-8')
                            self.assertIn('data-tab="sim"',html)
                            self.assertIn('65人成员交易资料',html)
                        state=get('/api/trading/sim/state')
                        self.assertEqual(len(state['people']),65)
                        self.assertEqual(state['metrics']['active_holdings'],0)
                        self.assertEqual(state['transactions'],[])
                        self.assertFalse(Path(folder,'trading-65.json').exists(), 'Read must not invent persisted trades')
                        post('eligibility',person_id='01',opened=True,currency='RON',funds=200,
                             frequency='HIGH',required_today=True)
                        out=post('create_offer',symbol='TEST',name='演练',market='BVB',currency='RON',
                                 unit_price=10,min_shares=5,hold_days=2,participant_count=4,discount_pct=0)
                        oid=out['result']['id']
                        day=state['market_date']
                        r=post('recommend',offer_id=oid,date=day)['result']
                        self.assertEqual(len(r['candidates']),1)
                        with self.assertRaises(HTTPError) as ex:
                            post('buy',offer_id=oid,person_id='01',date=day,quantity=5)
                        self.assertEqual(ex.exception.code,400)
                        post('invite',offer_id=oid,date=day,person_id='01')
                        out=post('buy',offer_id=oid,date=day,person_id='01',quantity=5)
                        hid=out['result']['holding']['id']
                        shot=get('/api/trading/sim/snapshot?date='+day+'&offer_id='+oid)
                        self.assertTrue(any(x['kind']=='holding' and x['character_id']=='01' for x in shot['facts']))
                        with self.assertRaises(HTTPError):
                            post('sell',holding_id=hid,sell_price=12)
                        state=get('/api/trading/sim/state')
                        self.assertEqual(state['metrics']['active_holdings'],1)
                        self.assertEqual([x['type'] for x in state['transactions']],['buy'])
                        self.assertEqual(json.loads(Path(folder,'trading-65.json').read_text())['roster_source'],'finance-director-65-v4.1')
                    finally:
                        server.shutdown();thread.join(timeout=5)

if __name__=='__main__':unittest.main()