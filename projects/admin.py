from django.contrib import admin
from .models import Project, Task
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1  # how many blank tasks to show by default

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'created_by', 'total_cost_display')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name',)

    # ✅ only show projects the user owns (Team Lead)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'TEAM_LEAD':
            return qs.filter(created_by=request.user)
        return qs.none()

    # ✅ automatically assign the creator when saving
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.save()

    def total_cost_display(self, obj):
        return f"${obj.total_cost():.2f}"
    total_cost_display.short_description = "Total Cost"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'cost', 'completed')
    list_filter = ('project', 'completed')
    search_fields = ('title',)

    # ✅ Restrict tasks to only those related to projects the team lead owns
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'TEAM_LEAD':
            return qs.filter(project__created_by=request.user)
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'STAFF':
            return qs.filter(assigned_to=request.user)
        return qs.none()
