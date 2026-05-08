from view.base_view import BaseView

_COL = f"  {'ID':<10} {'시료명':<20} {'생산시간(min)':<14} {'수율':<8} {'재고(ea)'}"
_SEP = "  " + "-" * 60


class SampleView(BaseView):
    def get_register_input(self) -> dict:
        print("\n--- 시료 등록 ---")
        sample_id = input("시료 ID (예: S-001): ").strip()
        name = input("시료명: ").strip()
        avg_production_time = float(input("평균 생산시간 (min/ea): ").strip())
        yield_rate = float(input("수율 (0.0~1.0): ").strip())
        stock = int(input("초기 재고 (ea, 기본 0): ").strip() or "0")
        return {
            "sample_id": sample_id,
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
            "stock": stock,
        }

    def show_sample_list(self, samples: list):
        self._show_sample_table("시료 목록", samples)

    def get_search_keyword(self) -> str:
        return input("검색어 입력: ").strip()

    def show_search_result(self, samples: list):
        self._show_sample_table("검색 결과", samples)

    def _show_sample_table(self, title: str, samples: list):
        print(f"\n--- {title} ---")
        if not samples:
            print("  해당 시료가 없습니다.")
            return
        print(_COL)
        print(_SEP)
        for s in samples:
            print(f"  {s.sample_id:<10} {s.name:<20} {s.avg_production_time:<14} {s.yield_rate:<8} {s.stock}")
