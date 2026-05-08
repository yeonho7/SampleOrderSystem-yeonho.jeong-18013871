from pathlib import Path

from model.order import OrderStatus
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.monitor_controller import MonitorController
from view.main_view import MainView
from view.sample_view import SampleView
from view.order_view import OrderView
from view.production_view import ProductionView
from view.monitor_view import MonitorView


class App:
    DATA_DIR = Path("data")

    def __init__(self):
        self.DATA_DIR.mkdir(exist_ok=True)
        sample_repo = SampleRepository(self.DATA_DIR / "samples.json")
        order_repo = OrderRepository(self.DATA_DIR / "orders.json")
        job_repo = ProductionJobRepository(self.DATA_DIR / "production_jobs.json")

        self._sample_ctrl = SampleController(sample_repo, order_repo)
        self._order_ctrl = OrderController(sample_repo, order_repo, job_repo)
        self._production_ctrl = ProductionController(sample_repo, order_repo, job_repo)
        self._monitor_ctrl = MonitorController(sample_repo, order_repo, job_repo)

        self._main_view = MainView()
        self._sample_view = SampleView()
        self._order_view = OrderView()
        self._production_view = ProductionView()
        self._monitor_view = MonitorView()

    def run(self):
        while True:
            self._main_view.show_header(self._get_summary())
            self._main_view.show_menu()
            choice = self._main_view.get_choice()

            if choice == "0":
                self._main_view.show_exit()
                break
            elif choice == "1":
                self._handle_sample()
            elif choice == "2":
                self._handle_reserve()
            elif choice == "3":
                self._handle_approve_reject()
            elif choice == "4":
                self._handle_monitor()
            elif choice == "5":
                self._handle_production()
            elif choice == "6":
                self._handle_release()
            else:
                self._main_view.show_invalid_choice()

    def _handle_sample(self):
        sub = self._sample_view.get_sub_choice()

        if sub == "1":
            try:
                data = self._sample_view.get_register_input()
                sample = self._sample_ctrl.register(**data)
                self._sample_view.show_message(f"시료 등록 완료: {sample.sample_id} ({sample.name})")
            except ValueError as e:
                self._sample_view.show_message(f"오류: {e}")
        elif sub == "2":
            self._sample_view.show_sample_list(self._sample_ctrl.find_all())
        elif sub == "3":
            keyword = self._sample_view.get_search_keyword()
            self._sample_view.show_search_result(self._sample_ctrl.search(keyword))
        else:
            self._sample_view.show_message("올바른 번호를 입력하세요.")

    def _handle_reserve(self):
        try:
            data = self._order_view.get_reserve_input()
            order = self._order_ctrl.reserve(**data)
            self._order_view.show_order_result(order)
        except ValueError as e:
            self._order_view.show_message(f"오류: {e}")

    def _handle_approve_reject(self):
        reserved = self._order_ctrl.list_reserved()
        self._order_view.show_reserved_list(reserved, self._sample_name_map())
        if not reserved:
            return

        sub = self._order_view.get_approve_reject_choice()

        if sub == "1":
            order_id = self._order_view.get_order_id_input("  승인할 주문번호: ")
            try:
                order = self._order_ctrl.approve(order_id)
                job = self._production_ctrl.find_job(order_id) if order.status == OrderStatus.PRODUCING else None
                self._order_view.show_approve_result(order, job)
            except ValueError as e:
                self._order_view.show_message(f"오류: {e}")
        elif sub == "2":
            order_id = self._order_view.get_order_id_input("  거절할 주문번호: ")
            try:
                order = self._order_ctrl.reject(order_id)
                self._order_view.show_reject_result(order)
            except ValueError as e:
                self._order_view.show_message(f"오류: {e}")
        else:
            self._order_view.show_message("올바른 번호를 입력하세요.")

    def _handle_monitor(self):
        sub = self._monitor_view.get_sub_choice()

        if sub == "1":
            self._monitor_view.show_order_stats(self._monitor_ctrl.get_order_stats())
        elif sub == "2":
            self._monitor_view.show_stock_status_all(self._monitor_ctrl.get_stock_status_all())
        else:
            self._monitor_view.show_message("올바른 번호를 입력하세요.")

    def _handle_production(self):
        current = self._production_ctrl.get_current()
        if current is None:
            self._production_view.show_no_current()
        else:
            sample = self._sample_ctrl.find_by_id(current.sample_id)
            self._production_view.show_current_job(current, sample)

        self._production_view.show_queue(self._production_ctrl.get_queue(), self._sample_name_map())

        if current is not None:
            ans = input("\n  현재 작업을 완료 처리하시겠습니까? (y/n): ").strip().lower()
            if ans == "y":
                try:
                    order = self._production_ctrl.complete_current()
                    self._production_view.show_complete_result(order)
                except ValueError as e:
                    self._production_view.show_message(f"오류: {e}")

    def _handle_release(self):
        confirmed = self._order_ctrl.list_confirmed()
        self._order_view.show_confirmed_list(confirmed, self._sample_name_map())
        if not confirmed:
            return

        order_id = self._order_view.get_order_id_input("  출고할 주문번호: ")
        try:
            order = self._order_ctrl.release(order_id)
            self._order_view.show_release_result(order)
        except ValueError as e:
            self._order_view.show_message(f"오류: {e}")

    def _get_summary(self) -> dict:
        return self._monitor_ctrl.get_summary()

    def _sample_name_map(self) -> dict:
        return {s.sample_id: s.name for s in self._sample_ctrl.find_all()}
