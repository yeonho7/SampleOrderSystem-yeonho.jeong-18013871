from datetime import datetime

from view.base_view import BaseView

_COL = f"  {'번호':<5} {'주문번호':<22} {'고객명':<15} {'시료명':<20} {'수량':>6} {'상태'}"
_SEP = "  " + "-" * 76


class OrderView(BaseView):
    def get_reserve_input(self) -> dict:
        print("\n--- 시료 주문 접수 ---")
        sample_id = input("시료 ID: ").strip()
        customer_name = input("고객명: ").strip()
        quantity = int(input("주문 수량 (ea): ").strip())
        return {
            "sample_id": sample_id,
            "customer_name": customer_name,
            "quantity": quantity,
        }

    def show_order_result(self, order):
        print(f"\n  주문 접수 완료")
        print(f"  주문번호 : {order.order_id}")
        print(f"  상태     : {order.status.value}")

    def show_reserved_list(self, orders: list, sample_name_map: dict):
        self._show_order_table("접수 대기 주문 목록 (RESERVED)", orders, sample_name_map)

    def get_order_id_input(self, prompt: str = "주문번호 입력: ") -> str:
        return input(prompt).strip()

    def show_approve_result(self, order, job=None):
        print(f"\n  주문 승인 완료")
        print(f"  주문번호 : {order.order_id}")
        print(f"  상태     : {order.status.value}")
        if job is not None:
            print(f"  [재고 부족 - 생산 등록]")
            print(f"  부족분        : {job.shortage}ea")
            print(f"  실 생산량     : {job.actual_production}ea")
            print(f"  예상 생산시간 : {job.total_time:.1f}분")

    def show_reject_result(self, order):
        print(f"\n  주문 거절 완료")
        print(f"  주문번호 : {order.order_id}")
        print(f"  상태     : {order.status.value}")

    def show_confirmed_list(self, orders: list, sample_name_map: dict):
        self._show_order_table("출고 대기 주문 목록 (CONFIRMED)", orders, sample_name_map)

    def show_release_result(self, order):
        print(f"\n  출고 처리 완료")
        print(f"  주문번호   : {order.order_id}")
        print(f"  출고 수량  : {order.quantity}ea")
        print(f"  처리 일시  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  상태       : {order.status.value}")

    def _show_order_table(self, title: str, orders: list, sample_name_map: dict):
        print(f"\n--- {title} ---")
        if not orders:
            print("  해당 주문이 없습니다.")
            return
        print(_COL)
        print(_SEP)
        for i, o in enumerate(orders, 1):
            name = sample_name_map.get(o.sample_id, o.sample_id)
            print(f"  {i:<5} {o.order_id:<22} {o.customer_name:<15} {name:<20} {o.quantity:>6} {o.status.value}")
