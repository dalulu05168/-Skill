"""In-memory screenplay staging and opt-in SQLite history adapter.

Rehearsal history is derived ONLY from earlier structurally accepted drafts
within this process. Staging is NOT adopting fictional scenes as official memory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from director_storygate import execute, OK
from scene_memory import person_history, STORY_ID


class SandboxSession:
    def __init__(self, roster):
        if roster.get("story_id")!=STORY_ID or roster.get("status")!="DRAFT_NOT_APPROVED":
            raise ValueError("only independent unapproved candidate roster supported")
        self.roster=roster
        self._staged=[]
        self._scene_ids=set()

    def make(self, request, model_fn=None):
        if request.get("scene_id") in self._scene_ids:
            raise ValueError("scene_id has already been staged; cannot overwrite")
        result=execute(self.roster,request,model_fn=model_fn,history=self._staged[-50:])
        if result["state"]=="EDITORIAL_REVIEW_REQUIRED":
            # Structural QA is not permission to publish or to write official memory.
            for m in result["draft"]["messages"]:
                self._staged.append({
                    "scene_id":request["scene_id"],"message_id":m["message_id"],
                    "speaker_id":m["speaker_id"],"text":m["text"],
                    "provenance":"SAME_RUN_SANDBOX"})
            self._scene_ids.add(request["scene_id"])
        return result

    def staged_count(self):
        return len(self._staged)

    def staged_summary(self):
        return {"scenes":len(self._scene_ids),"staged_messages":len(self._staged),
                "formal_memory_written":False,"publishable":False,
                "semantic_and_linguistic_review_still_required":True}


def approved_sqlite_history(db_path, approved_roster_path, speaker_ids, *, each_limit=5):
    """Read only genuinely approved SQLite memory for named approved speakers.

    Cannot use draft/legacy roster, cannot adopt stories, no transactions.
    """
    if type(each_limit) is not int or not 1<=each_limit<=10:
        raise ValueError("each_limit must be 1-10")
    roster=json.loads(Path(approved_roster_path).read_text(encoding="utf-8"))
    if roster.get("story_id")!=STORY_ID or not isinstance(roster.get("characters"),list):
        raise ValueError("wrong independent approved roster")
    known={p["id"] for p in roster["characters"] if p.get("approved_by_user") is True}
    if not known or any(p.get("approved_by_user") is not True for p in roster["characters"]):
        raise ValueError("new characters must be approved first")
    if not isinstance(speaker_ids,list) or len(speaker_ids)>15:
        raise ValueError("speaker_ids must be a bounded list")
    if any(sid not in known|{"assistant","professor"} for sid in speaker_ids):
        raise ValueError("cannot read history for unapproved character")
    history=[]
    for speaker in dict.fromkeys(speaker_ids):
        for row in person_history(db_path,approved_roster_path,speaker,limit=each_limit):
            history.append({"scene_id":row["scene_id"],"message_id":row["message_id"],
                            "speaker_id":row["speaker_id"],"text":row["text"],
                            "provenance":"ADOPTED_SQLITE"})
    if len(history)>50:raise ValueError("history exceeds prompt cap")
    return history
