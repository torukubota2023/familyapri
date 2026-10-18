"""model.py を使って全シナリオを計算し results.json と標準出力に書く"""
import json
from model import *

out = {}
# 1) 総負担（名目、運用益なし）
tot = {}
for n in (25, 30):
    for k in LOANS:
        if "19年" in k: continue
        t = totals(n, k)
        tot[f"{n}年/{k}"] = {kk: round(v, 1) for kk, v in t.items()}
out["totals"] = tot

# 2) 賃貸の総額（月額×上昇率）
rent_tot = {}
for n in (25, 30):
    for r0 in (12, 14, 16, 18):
        for g in (0.005, 0.02):
            rent_tot[f"{n}年/{r0}万/{g*100:.1f}%"] = round(sum(r0 * (1 + g) ** y * 12 for y in range(n)) + 300, 1)
out["rent_totals_incl300"] = rent_tot

# 3) 損益分岐家賃（初年度月額, 万円）
be = {}
for inv in (0.0, 0.01, 0.03):
    for n in (25, 30):
        for k in LOANS:
            if "19年" in k: continue
            for g in (0.005, 0.02):
                for sale in (2000, 3000, 4000):
                    be[f"運用{inv*100:.0f}%/{n}年/{k}/家賃上昇{g*100:.1f}%/売却{sale}"] = round(breakeven_rent(n, sale, g, k, inv), 2)
out["breakeven"] = be

# 4) 指定家賃での差額（購入有利額, 万円, 運用なし）
diff = {}
for n in (25, 30):
    for k in LOANS:
        for g in (0.005, 0.02):
            for sale in (2000, 3000, 4000):
                for r0 in (12, 14, 16, 18):
                    diff[f"{n}年/{k}/{g*100:.1f}%/売却{sale}/家賃{r0}"] = round(compare(n, sale, r0, g, k)[2])
out["advantage_buy"] = diff

# 5) 感応度（基本: 固定2%, 家賃上昇0.5%, 売却3000, 運用なし）
sens = {}
base = dict()
cases = {
    "基本": {},
    "維持費 初年度80万": dict(maint_first=80),
    "維持費の上昇 年3%": dict(maint_g=0.03),
    "大規模修繕の追加徴収 100万×2回(12年目・24年目)": dict(extra={11: 100, 23: 100}),
    "駐車場代を購入側に月1万円追加": dict(parking=1),
    "賃貸追加費用 30年は360万(年12万換算)": None,
    "賃貸追加費用 0円(更新料なし・転居なし)": dict(rent_extra=0),
    "賃貸追加費用 500万": dict(rent_extra=500),
}
for n in (25, 30):
    for name, kw in cases.items():
        if kw is None:
            kw = dict(rent_extra=300 if n == 25 else 360)
        for sale in (2000, 3000, 4000):
            sens[f"{n}年/{name}/売却{sale}"] = round(breakeven_rent(n, sale, 0.005, "固定2%", 0.0, **kw), 2)
out["sensitivity_breakeven"] = sens

# 6) 期末後: 25年・30年時点の月額住居費
after = {}
for n in (25, 30):
    after[f"{n}年目の購入側 維持費/月"] = round(60 * 1.02 ** (n - 1) / 12, 2)
    after[f"{n}年目の購入側 維持費/月(80万,3%)"] = round(80 * 1.03 ** (n - 1) / 12, 2)
    for r0 in (12, 14, 16, 18):
        for g in (0.005, 0.02):
            after[f"{n}年目の家賃/月 {r0}万 {g*100:.1f}%"] = round(r0 * (1 + g) ** (n - 1), 2)
out["after"] = after

# 7) 現在価値換算の参考（物価上昇率2%・1%で割り引く）
pvd = {}
for n in (25, 30):
    for sale in (2000, 3000, 4000):
        for inf in (0.01, 0.02):
            pvd[f"{n}年後の売却{sale}万 → 今の価値(物価{inf*100:.0f}%/年)"] = round(pv(sale, n, inf))
out["pv"] = pvd

# 8) 運用ありの期末純資産（例: 14万, 0.5%, 固定2%）
wl = {}
for inv in (0.0, 0.01, 0.03):
    for n in (25, 30):
        for sale in (2000, 3000, 4000):
            b, r, a = compare(n, sale, 14, 0.005, "固定2%", inv)
            wl[f"運用{inv*100:.0f}%/{n}年/売却{sale}"] = dict(購入側=round(b), 賃貸側=round(r), 購入有利=round(a))
out["wealth_14man"] = wl

# 9) 修正案（現実寄り）: 固定3.5%・維持費80万(駐車場込み)・賃貸追加費用は期間に比例(25年300万/30年360万)
real = {}
for inv in (0.0, 0.01, 0.03):
    for n in (25, 30):
        for g in (0.005, 0.02):
            for sale in (2000, 3000, 4000):
                real[f"運用{inv*100:.0f}%/{n}年/家賃上昇{g*100:.1f}%/売却{sale}"] = round(breakeven_rent(
                    n, sale, g, "固定3.5%", inv, maint_first=80, rent_extra=300 if n == 25 else 360), 2)
out["realistic_breakeven"] = real

# 10) 年次の月額支出（グラフ用）
yearly = {}
for k in LOANS:
    yearly[f"購入 {k}"] = [round(sum(buy_monthly(30, k)[y*12:(y+1)*12]) / 12, 2) for y in range(30)]
for r0 in (14,):
    for g in (0.005, 0.02):
        yearly[f"賃貸 {r0}万 {g*100:.1f}%"] = [round(r0 * (1 + g) ** y, 2) for y in range(30)]
out["yearly_monthly"] = yearly

json.dump(out, open("results.json", "w"), ensure_ascii=False, indent=1)
for sec, d in out.items():
    print("==", sec)
    for k, v in d.items():
        print(k, v)
