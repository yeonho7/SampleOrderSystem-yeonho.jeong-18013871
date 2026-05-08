from model.order import OrderStatus
from view.base_view import BaseView

_LABELS = {
    OrderStatus.RESERVED: "접수 대기 (RESERVED)",
    OrderStatus.PRODUCING: "생산 중   (PRODUCING)",
    OrderStatus.CONFIRMED: "출고 대기 (CONFIRMED)",
    OrderStatus.RELEASE:   "출고 완료 (RELEASE)  ",
}
_SEP = "  " + "-" * 50


class MonitorView(BaseView):
    def show_order_stats(self, stats: dict):
        print("\n--- 주문량 현황 ---")
        for status, label in _LABELS.items():
            print(f"  {label} : {stats.get(status, 0)}건")

    def show_stock_status_all(self, stock_statuses: list):
        print("\n--- 재고 현황 ---")
        if not stock_statuses:
            print("  등록된 시료가 없습니다.")
            return
        print(f"  {'시료 ID':<12} {'시료명':<20} {'재고(ea)':>8}  {'상태'}")
        print(_SEP)
        for entry in stock_statuses:
            s = entry["sample"]
            print(f"  {s.sample_id:<12} {s.name:<20} {s.stock:>8}  {entry['status']}")
