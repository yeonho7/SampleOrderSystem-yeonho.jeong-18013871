from model.order import OrderStatus


class MonitorView:
    def show_order_stats(self, stats: dict):
        print("\n--- 주문량 현황 ---")
        labels = {
            OrderStatus.RESERVED: "접수 대기 (RESERVED)",
            OrderStatus.PRODUCING: "생산 중  (PRODUCING)",
            OrderStatus.CONFIRMED: "출고 대기 (CONFIRMED)",
            OrderStatus.RELEASE:  "출고 완료 (RELEASE)  ",
        }
        for status, label in labels.items():
            count = stats.get(status, 0)
            print(f"  {label} : {count}건")

    def show_stock_status_all(self, stock_statuses: list):
        print("\n--- 재고 현황 ---")
        if not stock_statuses:
            print("  등록된 시료가 없습니다.")
            return
        print(f"  {'시료 ID':<12} {'시료명':<20} {'재고(ea)':>8}  {'상태'}")
        print("  " + "-" * 50)
        for entry in stock_statuses:
            sample = entry["sample"]
            status = entry["status"]
            print(f"  {sample.sample_id:<12} {sample.name:<20} {sample.stock:>8}  {status}")

    def show_message(self, msg: str):
        print(f"  {msg}")
