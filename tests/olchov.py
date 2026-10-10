"""O'lchov: namunalar to'plamida aniqlik va tezlik jadvali.

    python3 tests/olchov.py                          # 15 asosiy namuna, faqat qoidalar
    python3 tests/olchov.py tests/yashirin_namunalar.json --ai   # yashirin to'plam, AI bilan

«Yashirin» to'plam qoidalar yozilishidan oldin, qoidalarni ko'rmagan alohida agent tomonidan yozilgan —
bot unga moslab sozlanmagan, shuning uchun u haqiqiy umumlashtirishni ko'rsatadi.
"""
import json
import statistics
import sys
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ILDIZ))
from bot import check  # noqa: E402


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fayl = Path(args[0]) if args else ILDIZ / "tests" / "namunalar.json"
    ai_yoqiq = "--ai" in sys.argv
    namunalar = json.loads(fayl.read_text("utf-8"))
    togri = aniq = otkazildi = yolgon_qizil = 0
    eng_sekin = 0.0
    vaqtlar, ai_soni = [], 0
    for n in namunalar:
        r = check.tekshir(n["matn"], n.get("fayl"), ai_yoqiq=ai_yoqiq)
        k = n["kutilgan"]
        ok = r.daraja == "toza" if k == "toza" else r.daraja in ("xavfli", "shubhali")
        togri += ok
        aniq += r.daraja == k
        otkazildi += k != "toza" and r.daraja == "toza"
        yolgon_qizil += k == "toza" and r.daraja == "xavfli"
        eng_sekin = max(eng_sekin, r.soniya)
        vaqtlar.append(r.soniya)
        ai_soni += r.pogona == 4
        print(f"{n['id']:4} {k:8} → {r.daraja:8} p{r.pogona} {r.soniya:5.2f}s {r.manba:24} {'OK ' if ok else 'XATO'} "
              f"{','.join(r.belgilar)[:60]}")
        if not ok:
            print("      " + n["matn"][:150].replace("\n", " "))
    jami = len(namunalar)
    print(f"\nTo'g'ri: {togri}/{jami} · aniq daraja: {aniq}/{jami} · o'tkazib yuborilgan firibgarlik: {otkazildi} · "
          f"toza xabarga 🔴: {yolgon_qizil} · eng sekin javob: {eng_sekin:.2f}s · median: {statistics.median(vaqtlar):.2f}s · "
          f"AI'ga borgan: {ai_soni}/{jami} · AI: {'yoqiq' if ai_yoqiq else 'yo‘q'}")


if __name__ == "__main__":
    main()
