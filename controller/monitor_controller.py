from model.order import OrderStatus


class MonitorController:
    def __init__(self, sample_repo, order_repo):
        self._sample_repo = sample_repo
        self._order_repo = order_repo

    def get_order_stats(self) -> dict:
        tracked = [
            OrderStatus.RESERVED,
            OrderStatus.PRODUCING,
            OrderStatus.CONFIRMED,
            OrderStatus.RELEASE,
        ]
        result = {status: 0 for status in tracked}
        for order in self._order_repo.find_all():
            if order.status in result:
                result[order.status] += 1
        return result

    def get_stock_status_all(self) -> list:
        pending_statuses = (OrderStatus.RESERVED, OrderStatus.PRODUCING)
        orders = self._order_repo.find_all()
        result = []
        for sample in self._sample_repo.find_all():
            if sample.stock == 0:
                status = "고갈"
            else:
                pending = sum(
                    o.quantity
                    for o in orders
                    if o.sample_id == sample.sample_id and o.status in pending_statuses
                )
                status = "부족" if sample.stock < pending else "여유"
            result.append({"sample": sample, "status": status})
        return result

    def get_summary(self) -> dict:
        samples = self._sample_repo.find_all()
        orders = self._order_repo.find_all()
        non_rejected = [o for o in orders if o.status != OrderStatus.REJECTED]
        producing_count = sum(1 for o in orders if o.status == OrderStatus.PRODUCING)
        return {
            "sample_count": len(samples),
            "total_stock": sum(s.stock for s in samples),
            "order_count": len(non_rejected),
            "queue_size": producing_count,
        }
