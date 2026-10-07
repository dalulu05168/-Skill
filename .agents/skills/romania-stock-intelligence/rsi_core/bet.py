"""BET constituent contribution estimate using given, evidence-linked inputs.

Not the official BVB calculation: adjustments, float factors, corporate actions,
rebalances and point-in-time weights require official methodology/data.
"""
from .common import DataError, nonempty, number, timestamp, web_url


def analyze_bet(doc):
    if doc.get("index") != "BET":
        raise DataError("Only BET (price-return) supported, never BET-TR")
    basis = doc.get("weights_basis")
    if basis not in ("prior_close", "other"):
        raise DataError("weights_basis must be prior_close or other")
    time = timestamp(doc.get("returns_as_of"), doc.get("timezone", "Europe/Bucharest"), "returns_as_of")
    wt = timestamp(doc.get("weights_as_of"), doc.get("timezone", "Europe/Bucharest"), "weights_as_of")
    if wt > time:
        raise DataError("weights_as_of cannot be after returns_as_of")
    url_weights = web_url(doc.get("weights_source_url"), "weights_source_url")
    url_returns = web_url(doc.get("returns_source_url"), "returns_source_url")
    rows = doc.get("constituents")
    if not isinstance(rows, list) or not rows:
        raise DataError("non-empty constituents array required")
    total, changes, seen, out = 0.0, 0.0, set(), []
    for i, c in enumerate(rows):
        ticker = nonempty(c.get("ticker"), f"constituents[{i}].ticker").upper()
        if ticker in seen:
            raise DataError(f"duplicate constituent {ticker}")
        seen.add(ticker)
        w = number(c.get("weight_pct"), f"{ticker}.weight_pct")
        r = number(c.get("return_pct"), f"{ticker}.return_pct")
        if not 0 < w <= 100 or r < -100:
            raise DataError(f"invalid constituent weight/return: {ticker}")
        contribution = w * r / 100.0
        changes += contribution
        total += w
        out.append({"ticker":ticker, "sector":nonempty(c.get("sector"), f"{ticker}.sector"), "weight_pct":w, "return_pct":r, "contribution_pp":round(contribution, 6)})
    if total > 100.5:
        raise DataError(f"weights sum to {total:.3f}% (>100.5%); conflicting weights")
    complete = 99.5 <= total <= 100.5 and doc.get("complete_roster") is True
    if doc.get("complete_roster") is True and not complete:
        raise DataError("complete_roster asserted but weight sum not near 100%")
    pos = sorted((r for r in out if r["contribution_pp"] > 0), key=lambda r:r["contribution_pp"], reverse=True)
    neg = sorted((r for r in out if r["contribution_pp"] < 0), key=lambda r:r["contribution_pp"])
    positive_total = sum(x["contribution_pp"] for x in pos)
    concentration = (sum(x["contribution_pp"] for x in pos[:3]) / positive_total * 100) if positive_total > 0 else None
    basis_usable = basis == "prior_close" and complete
    flags = ["估算：不是交易所公布的正式成分贡献。可能受成分调整、复权、权重时间不匹配等影响。"]
    if not complete: flags.append("成分或权重覆盖不完整，只能报告样本贡献，不得标为完整 BET 归因。")
    if basis != "prior_close": flags.append("权重并非上一个收盘时点，贡献估计误差可能较大。")
    if doc.get("actual_index_return_pct") is not None:
        official_return = number(doc["actual_index_return_pct"], "actual_index_return_pct")
        web_url(doc.get("actual_index_source_url"), "actual_index_source_url")
        diff = changes - official_return
        flags.append(f"贡献估计与输入的指数回报差 {diff:+.4f} 百分点，不能强行归因。")
    return {"index":"BET", "estimate_type":"weighted_return_approximation", "weights_basis":basis, "as_of":time.isoformat(), "weights_as_of":wt.isoformat(), "weights_source_url":url_weights, "returns_source_url":url_returns, "complete":complete, "weight_coverage_pct":round(total,4), "estimated_total_return_pct":round(changes,6) if complete else None, "observed_subset_contribution_pp":round(changes,6), "advancers":sum(x["return_pct"]>0 for x in out), "decliners":sum(x["return_pct"]<0 for x in out), "unchanged":sum(x["return_pct"]==0 for x in out), "top_3_share_of_positive_contribution_pct":round(concentration,3) if concentration is not None else None, "top_positive":pos[:5], "top_negative":neg[:5], "constituents":out, "qualified_full_index_attribution":basis_usable, "limitations":flags}
