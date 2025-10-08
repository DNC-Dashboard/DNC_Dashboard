# apps/pages/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Max
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()  # shared board (everyone sees the same)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Put new cards at the bottom of their column
        status = self.request.data.get("status") or Task.Status.BACKLOG
        last = Task.objects.filter(status=status).aggregate(m=Max("order"))["m"] or 0
        serializer.save(created_by=self.request.user, status=status, order=last + 1)

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """
        Optional helper to reorder within columns later.
        payload: {"status":"todo","order":5}
        """
        task = self.get_object()
        status = request.data.get("status", task.status)
        order  = int(request.data.get("order", task.order))

        # shift orders inside target column
        Task.objects.filter(status=status, order__gte=order).update(order=models.F("order") + 1)

        task.status = status
        task.order  = order
        task.save(update_fields=["status", "order"])
        return Response(TaskSerializer(task).data)
