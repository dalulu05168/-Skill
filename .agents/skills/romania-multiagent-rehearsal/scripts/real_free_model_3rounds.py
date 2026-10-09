"""Three-round REAL CPU-local Ollama screenplay rehearsal with 5 recurring actors.

Read each actor's *full* v4.1 original JSON and compose prompts by their
identity, behavioral, emotional, language and prior-story details.
The same five characters meet across three rounds to test story continuity.
Open model outputs are internal fictional drafts, never investor testimony.
No news numbers, paid provider API, WhatsApp publishing or memory/state writes.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

from engine import registry
from ollama_free_rehearsal import query_model, safety_flags

TEST_CAST = ("01", "06", "15", "38", "57")
TEST_TOPICS = (
    "Cum se deosebeşte diversificarea de simplul număr de acţiuni?",
    "Dacă două companii depind de acelaşi factor economic, riscul este cu adevărat separat?",
    "Ce întrebare rămasă fără răspuns ai verifica înainte să-ţi formezi o opinie?"
)


def info_for_model(person: dict) -> dict:
    """Use and preserve the original nested fields rather than a simplified panel."""
    src = person["source_profile"]
    ext = person["identity_extension"]
    lang = person["language_dna"]
    media = lang.get("媒体行为管理_v4", {})
    return {
        "id":person["character_id"],"name":ext.get("姓名"),
        "age":src.get("年龄"),"job":src.get("工作_职业"),
        "city":ext.get("居住城市"),
        "language":lang.get("角色语言执行_v4_1",{}).get("母语或优先输出语言","unknown"),
        "personality":person.get("personality",{}).get("核心标签",[]),
        "investing_knowledge_score":person.get("investment_profile",{}).get("知识总分"),
        "investment_experiences":person.get("investment_history",{}),
        "emotional_baseline":person.get("emotion_model",{}).get("默认状态"),
        "speech_style":lang.get("典型结构",""),
        "usual_length":lang.get("正常发言长度",""),
        "personal_romanian_phrases":lang.get("罗马尼亚短语",[]),
        "emoji_preference":lang.get("表情习惯",{}).get("常用",[]),
        "gif_permitted":media.get("媒体许可策略",{}).get("GIF",False),
        "relationships":person.get("relationship_network",[])[:5],
        "speech_triggers":person.get("speech_triggers") or person.get("activity_pattern",{}),
        "memory_guidance":person.get("memory_system",{})
    }


def instruction(c:dict, topic:str, round_number:int,
                prior_words:list[str], recent_group:list[str]) -> str:
    if c["language"] != "ro-RO":
        raise ValueError("This Romanian-only smoke scene requires ro-RO characters")
    persona = {
       "name":c["name"],"age":c["age"],"profession":c["job"],
       "home":c["city"],"traits":c["personality"][:6],
       "thinking_style":c["speech_style"],"length":c["usual_length"],
       "prior":str(c["investment_experiences"])[:220],
       "emoji":c["emoji_preference"][:4],
       "general_emotion":c["emotional_baseline"],
       "knowledge_score":c["investing_knowledge_score"]
    }
    other_lines = "\n".join(recent_group[-3:]) or "(începutul discuţiei)"
    own_lines = "\n".join(prior_words[-2:]) or "(nu ai vorbit încă)"
    return f"""You are writing ONE message in a clearly FICTIONAL educational screenplay.
A realistic adult Romanian character speaks in informal Romanian, not in Chinese.
Persona data (do not print this JSON): {json.dumps(persona,ensure_ascii=False)}
Your own fictional previous lines: {own_lines}
Other characters' latest fictional comments: {other_lines}
Round {round_number}, teacher's subject: {topic}
Think and respond to what someone just said; a question or disagreement is fine.
Retain memory of what you said earlier, but do not repeat the sentence.
Write ONE Romanian-language line of 3-23 words, conversational, usually one
sentence; optional greeting, at most ONE emoji only if natural for your character.
No role label, no quotes around the line, no markdown, no made-up statistics,
earnings or client testimonials, no particular stock advice, no buy/sell order.
Remember this is a simulation, NOT real investors in a WhatsApp group.
MESSAGE IN ROMANIAN ONLY:"""


def text_issues(text:str, earlier:list[str], c:dict)->list[str]:
    flags=safety_flags(text)
    if re.search(r"[\u4E00-\u9FFF]",text):
        flags.append("contains_chinese_not_romanian")
    if len(text.split()) > 35 or len(text.strip()) < 3:
        flags.append("bad_message_length")
    if text.strip().casefold() in [x.strip().casefold() for x in earlier]:
        flags.append("duplicate_message")
    if not re.search("[ăâîșşțţ]",text,flags=re.I):
        flags.append("romanian_diacritics_not_detected_check_manually")
    return flags


def produce(model:str, output:Path,*, llm=query_model, ids=TEST_CAST)->dict:
    all_personas=registry()
    if len(all_personas)!=65 or len(ids)!=5 or len(set(ids))!=5:
        raise ValueError("Exact original 65 + exactly five unique test actors required")
    cast=[info_for_model(all_personas[p]) for p in ids]
    if any(x["language"]!="ro-RO" for x in cast):
        raise ValueError("One test actor is primarily not Romanian-speaking")
    own={p:[] for p in ids}
    recent=[]
    rounds=[]
    attempted=0
    for index,topic in enumerate(TEST_TOPICS,1):
        turns=[]
        for c in cast:
            prompt=instruction(c,topic,index,own[c["id"]],recent)
            try:
                line=llm(prompt=prompt,model=model).strip()
                attempted+=1
                flags=text_issues(line,own[c["id"]],c)
                status="NEEDS_HUMAN_REVIEW" if not flags else "NEEDS_CORRECTION"
                own[c["id"]].append(line)
                recent.append(f'{c["name"]}: {line}')
            except Exception as exc:
                line=None
                flags=["MODEL_CALL_ERROR_"+type(exc).__name__]
                status="FAILED"
            turns.append({"id":c["id"],"name":c["name"],"language":c["language"],
                          "utterance":line,"flags":flags,"status":status,
                          "previous_self_turns":index-1,"publication_allowed":False})
            print("TRIAL",index,c["id"],status,repr(line),flush=True)
        rounds.append({"round":index,"topic":topic,"messages":turns,
                       "publication_allowed":False})
    report={
      "simulation":"FICTIONAL_EDUCATIONAL_REHEARSAL_ONLY",
      "source":"Original v4.1 JSON from 65-persona GitHub bank",
      "model":model,"real_model_calls_succeeded":attempted,
      "expected_model_calls":15,
      "simulated_role_count":67,
      "character_count_loaded":len(all_personas),
      "unique_test_characters":len(cast),
      "same_five_roles_across_rounds":True,
      "user_adopted_memory_changed":False,
      "simulation_state_temporary":True,
      "publish_allowed":False,
      "whatsapp_sent":False,
      "requires_human_romanian_review":True,
      "rounds":rounds
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:
        os.chmod(output,0o600)
        json.dump(report,f,ensure_ascii=False,indent=2)
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="qwen2.5:1.5b")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.model not in ("qwen2.5:1.5b","qwen2.5:0.5b"):
        raise SystemExit("Only approved free local models")
    r=produce(a.model,a.output)
    print("SUMMARY",json.dumps({
      "actual_model_calls":r["real_model_calls_succeeded"],
      "source_persona_count":r["character_count_loaded"],
      "test_persona_count":r["unique_test_characters"],
      "three_rounds_completed":len(r["rounds"])==3,
      "model_failed_messages":sum(m["status"]=="FAILED" for x in r["rounds"] for m in x["messages"]),
      "messages_flagged":sum(m["status"]=="NEEDS_CORRECTION" for x in r["rounds"] for m in x["messages"]),
      "final_quality_approved":False,
      "publication_allowed":False
    },ensure_ascii=False),flush=True)
    if r["real_model_calls_succeeded"]!=15:
        raise SystemExit("INCOMPLETE: see simulation artifact, model failures")

if __name__=="__main__":
    main()
