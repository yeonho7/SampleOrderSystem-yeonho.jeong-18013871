from datetime import datetime

from view.base_view import BaseView

_BORDER = "=" * 50


class MainView(BaseView):
    def show_header(self, summary: dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(_BORDER)
        print("  S-Semi 반도체 시료 생산주문관리 시스템")
        print(_BORDER)
        print(f"  현재 시각     : {now}")
        print(f"  등록 시료 종수 : {summary['sample_count']}종")
        print(f"  총 재고       : {summary['total_stock']}ea")
        print(f"  전체 주문 건수 : {summary['order_count']}건")
        print(f"  생산라인 대기  : {summary['queue_size']}건")
        print(_BORDER)

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

    def show_invalid_choice(self):
        print("  올바른 메뉴 번호를 입력하세요.")

    def show_exit(self):
        print("  시스템을 종료합니다.")
