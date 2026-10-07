"""Evidence-grounded deterministic Professor reasoning memo generator."""
from .common import DataError, nonempty, timestamp, web_url


def generate_lesson(data):
    title = nonempty(data.get("topic"), "topic")
    facts = data.get("facts")
    if not isinstance(facts, list) or not facts:
        raise DataError("At least one documented fact is required")
    lines = [f"# 教授研究课：{title}", "", "> 以下为基于输入证据的教学讨论，不构成投资指令或收益承诺。", "", "## 一、经引用的事实"]
    for i, fact in enumerate(facts):
        if not isinstance(fact, dict):
            raise DataError("fact must be an object")
        body = nonempty(fact.get("text"), f"facts[{i}].text")
        link = web_url(fact.get("source_url"))
        dt = timestamp(fact.get("observed_at"), fact.get("timezone", "Europe/Bucharest"), "observed_at")
        nonempty(fact.get("evidence_locator"), "evidence_locator")
        lines.append(f"- **[提供的事实（尚需独立核对源网页）]** {body}（来源：{link}；观察时间：{dt.isoformat()}；定位：{fact['evidence_locator']}）")
    mechanisms = data.get("mechanisms")
    if not isinstance(mechanisms,list) or not mechanisms:
        raise DataError("Mechanism steps are required; do not jump from headlines to returns")
    lines.extend(["", "## 二、可能的传导机制（分析假设）"])
    for n, item in enumerate(mechanisms,1):
        lines.append(f"{n}. {nonempty(item, 'mechanism')}")
    contrary = data.get("counterarguments")
    if not isinstance(contrary,list) or not contrary:
        raise DataError("At least one contrary explanation is required")
    lines.extend(["", "## 三、为什么这个判断可能不成立"])
    for item in contrary:
        lines.append(f"- {nonempty(item, 'counterargument')}")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios,dict) or set(scenarios) != {"favorable","base","adverse"}:
        raise DataError("Provide favorable/base/adverse scenarios, each with condition and implication")
    lines.extend(["", "## 四、条件情景（非价格预测）"])
    for key, label in [("favorable","有利情景"),("base","基准情景"),("adverse","不利情景")]:
        val = scenarios[key]
        if not isinstance(val,dict):
            raise DataError("scenario object required")
        condition = nonempty(val.get("condition"), "scenario.condition")
        implication = nonempty(val.get("implication"), "scenario.implication")
        lines.append(f"- **{label}**：如果{condition}，则可能{implication}。")
    checks = data.get("watch_next")
    if not isinstance(checks,list) or not checks:
        raise DataError("At least one falsifiable watch_next item is required")
    lines.extend(["", "## 五、下一步核验指标"])
    for item in checks:
        lines.append(f"- {nonempty(item, 'watch_next')}")
    lines.extend(["", "**教授提问：**哪些新证据会让我们主动修改今天的判断？", "", "*说明：事实准确性仍依赖对原始来源的独立核实，系统不会据此给出确定性买卖指令。*"])
    return "\n".join(lines) + "\n"
