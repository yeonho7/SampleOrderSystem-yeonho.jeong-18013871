from datetime import datetime


class MainView:
    def show_header(self, summary: dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("=" * 50)
        print("  S-Semi 반도체 시료 생산주문관리 시스템")
        print("=" * 50)
        print(f"  현재 시각     : {now}")
        print(f"  등록 시료 종수 : {summary['sample_count']}종")
        print(f"  총 재고       : {summary['total_stock']}ea")
        print(f"  전체 주문 건수 : {summary['order_count']}건")
        print(f"  생산라인 대기  : {summary['queue_size']}건")
        print("=" * 50)

    def show_menu(self):
        print()
        print("  1. 시료 관리")
        print("  2. 시료 주문 접수")
        print("  3. 주문 승인/거절")
        print("  4. 모니터링")
        print("  5. 생산라인 조회")
        print("  6. 출고 처리")
        print("  0. 종료")
        print()

    def get_choice(self) -> str:
        return input("메뉴 선택: ").strip()
