from view.base_view import BaseView

_COL = f"  {'순서':<5} {'주문번호':<22} {'시료명':<20} {'실 생산량':>10} {'부족분':>8}"
_SEP = "  " + "-" * 68


class ProductionView(BaseView):
    def show_current_job(self, job, sample=None):
        print("\n--- 현재 생산 중인 작업 ---")
        print(f"  주문번호     : {job.order_id}")
        if sample is not None:
            print(f"  시료명       : {sample.name}")
        else:
            print(f"  시료 ID      : {job.sample_id}")
        print(f"  실 생산량    : {job.actual_production}ea")
        print(f"  부족분       : {job.shortage}ea")
        print(f"  총 생산시간  : {job.total_time:.1f}분")

    def show_queue(self, jobs: list, sample_name_map: dict):
        print("\n--- 생산 대기 큐 ---")
        if not jobs:
            print("  대기 중인 작업이 없습니다.")
            return
        print(_COL)
        print(_SEP)
        for i, job in enumerate(jobs, 1):
            name = sample_name_map.get(job.sample_id, job.sample_id)
            print(f"  {i:<5} {job.order_id:<22} {name:<20} {job.actual_production:>10} {job.shortage:>8}")

    def show_no_current(self):
        print("\n  현재 생산 중인 작업이 없습니다.")

    def show_complete_result(self, order):
        print(f"\n  생산 완료 처리")
        print(f"  주문번호 : {order.order_id}")
        print(f"  상태     : {order.status.value}")
