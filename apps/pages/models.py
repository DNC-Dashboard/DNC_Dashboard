# apps/pages/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Task(models.Model):
    class Status(models.TextChoices):
        BACKLOG     = "backlog", "Backlog"
        TODO        = "todo", "To Do"
        INPROGRESS  = "inprogress", "In Progress"
        DONE        = "done", "Done"

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title      = models.CharField(max_length=120)
    desc       = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.BACKLOG)
    order      = models.PositiveIntegerField(default=0)  # position inside a column
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"
