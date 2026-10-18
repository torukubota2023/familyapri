"""那覇・賃貸 vs 購入 試算モデル（比較用の仮定条件。実際の資産・契約条件ではない）

金額の単位は万円。すべて「名目」（将来のその時点の額面）で計算し、
現在価値への換算は別関数で明示的に行う。
"""
import json

PRICE, DOWN, BUY_COST = 5000, 500, 350
LOAN, TERM_Y = 4500, 20


def payment(principal, annual_rate, months):
    r = annual_rate / 12
    if r == 0:
        return principal / months
    return principal * r / (1 - (1 + r) ** -months)


def loan_schedule(rates_by_year):
    """rates_by_year: 返済年数分の年利リスト（長さ＝返済期間）。金利が変わった年の初めに
    残高から返済額を再計算。月ごとの (返済額, 利息, 元本) を返す。"""
    n = len(rates_by_year) * 12
    bal, rows, cur_rate, pay = LOAN, [], None, None
    for m in range(n):
        y = m // 12
        rate = rates_by_year[y]
        if rate != cur_rate:
            cur_rate = rate
            pay = payment(bal, rate, n - m)
        interest = bal * rate / 12
        principal = pay - interest
        bal -= principal
        rows.append((pay, interest, principal))
    assert abs(bal) < 1e-6
    return rows


LOANS = {
    "固定2%": [0.02] * 20,
    "変動 2%→3%": [0.02] * 5 + [0.03] * 15,
    "変動 2%→4%": [0.02] * 5 + [0.04] * 15,
    # 修正案: 2026年10月の実勢に近い全期間固定（フラット35の20年以下の最低水準 約3.5%）
    "固定3.5%": [0.035] * 20,
    # 参考: 夫60歳申込ならフラット35の最長は19年（80−61）
    "固定3.5%・19年": [0.035] * 19,
}


def maint_monthly(n_years, first=60, g=0.02, extra=None):
    """維持費（月割り）。extra: {年index: 一時金} 大規模修繕の追加徴収など"""
    out = []
    for y in range(n_years):
        a = first * (1 + g) ** y
        for _ in range(12):
            out.append(a / 12)
        if extra and y in extra:
            out[-1] += extra[y]
    return out


def rent_monthly(n_years, rent0, g, extra_total):
    """家賃（年1回改定と仮定）＋ 更新・転居など追加費用を毎月均等に配分"""
    out = []
    for y in range(n_years):
        for _ in range(12):
            out.append(rent0 * (1 + g) ** y + extra_total / (n_years * 12))
    return out


def buy_monthly(n_years, loan_key, maint_first=60, maint_g=0.02, extra=None, parking=0):
    sched = loan_schedule(LOANS[loan_key])
    mt = maint_monthly(n_years, maint_first, maint_g, extra)
    out = []
    for m in range(n_years * 12):
        lp = sched[m][0] if m < len(sched) else 0
        out.append(lp + mt[m] + parking)
    return out


def compare(n_years, sale, rent0, rent_g, loan_key="固定2%", invest=0.0,
            rent_extra=300, maint_first=60, maint_g=0.02, extra=None, parking=0):
    """毎月、両者とも同じ予算（高い方の支出）を使い、安い側が差額を積み立てる。
    初期費用 850万円は購入側が支払い、賃貸側はそれを手元に残して運用。
    返り値: 期末の (購入側の純資産, 賃貸側の純資産, 購入有利額)。invest=0 なら単純合計比較と一致。"""
    b = buy_monthly(n_years, loan_key, maint_first, maint_g, extra, parking)
    r = rent_monthly(n_years, rent0, rent_g, rent_extra)
    mr = (1 + invest) ** (1 / 12) - 1
    fund_buy, fund_rent = 0.0, float(DOWN + BUY_COST)
    for m in range(n_years * 12):
        diff = b[m] - r[m]
        fund_buy *= 1 + mr
        fund_rent *= 1 + mr
        if diff > 0:
            fund_rent += diff
        else:
            fund_buy += -diff
    wealth_buy = fund_buy + sale
    wealth_rent = fund_rent
    return wealth_buy, wealth_rent, wealth_buy - wealth_rent


def totals(n_years, loan_key="固定2%", rent0=14, rent_g=0.005, rent_extra=300,
           maint_first=60, maint_g=0.02, extra=None, parking=0):
    sched = loan_schedule(LOANS[loan_key])
    loan_pay = sum(p for p, _, _ in sched)
    interest = sum(i for _, i, _ in sched)
    mt = sum(maint_monthly(n_years, maint_first, maint_g, extra)) + parking * 12 * n_years
    rent = sum(rent0 * (1 + rent_g) ** y * 12 for y in range(n_years))
    return dict(upfront=DOWN + BUY_COST, loan_total=loan_pay, interest=interest,
                principal=LOAN, maint=mt, buy_gross=DOWN + BUY_COST + loan_pay + mt,
                rent=rent, rent_extra=rent_extra, rent_gross=rent + rent_extra)


def breakeven_rent(n_years, sale, rent_g, loan_key="固定2%", invest=0.0, **kw):
    """購入側と賃貸側の期末純資産が等しくなる「初年度の月額家賃」（二分法）"""
    lo, hi = 0.0, 60.0
    for _ in range(60):
        mid = (lo + hi) / 2
        _, _, adv = compare(n_years, sale, mid, rent_g, loan_key, invest, **kw)
        # adv>0: 購入有利 → 家賃をもっと下げないと賃貸が勝てない…ではなく
        # 家賃が高いほど購入有利。adv(mid)=0 を探す
        if adv > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def pv(amount, years, rate):
    return amount / (1 + rate) ** years


if __name__ == "__main__":
    res = {}
    for k in LOANS:
        s = loan_schedule(LOANS[k])
        res[k] = dict(first=s[0][0] * 1e4, after5=s[60][0] * 1e4,
                      total=sum(p for p, _, _ in s), interest=sum(i for _, i, _ in s),
                      bal5=LOAN - sum(p for _, _, p in s[:60]))
    print(json.dumps(res, ensure_ascii=False, indent=1))
