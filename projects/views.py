from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Project, Profile, Task
from datetime import datetime
import json

@login_required
def projects_view(request):
    """Render the projects page"""
    return render(request, 'projects/projects.html')

@login_required
@require_http_methods(["GET"])
def get_projects(request):
    """Get projects based on user role and permissions"""
    user = request.user

    # Superuser sees all projects
    if user.is_superuser:
        projects = Project.objects.all()
    # Team leads see only their own projects
    elif user.profile.role == 'TEAM_LEAD':
        projects = Project.objects.filter(created_by=user)
    # Staff only see projects they're assigned to
    else:
        projects = Project.objects.filter(members=user)

    projects_data = []
    for project in projects:
        # Determine if user can edit this project
        can_edit = user.is_superuser or (user.profile.role == 'TEAM_LEAD' and project.created_by == user)

        projects_data.append({
            'id': project.id,
            'name': project.name,
            'description': project.description or '',
            'created': project.start_date.isoformat(),
            'cost': float(project.total_cost()),
            'staff': [member.id for member in project.members.all()],
            'created_by': project.created_by.id if project.created_by else None,
            'can_edit': can_edit
        })

    return JsonResponse({
        'projects': projects_data,
        'user_role': user.profile.role,
        'is_superuser': user.is_superuser
    })

@login_required
@require_http_methods(["GET"])
def get_staff_by_id(request, user_id):
    """Get staff member name by ID"""
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'role': user.profile.get_role_display()
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def get_staff_members(request):
    """Get all staff members for assignment dropdown"""
    user = request.user

    # Staff members can see the list (read-only), but only team leads can assign
    # Get all users with STAFF role
    staff_users = User.objects.filter(profile__role='STAFF').select_related('profile')

    staff_data = []
    for staff_user in staff_users:
        staff_data.append({
            'id': staff_user.id,
            'name': staff_user.get_full_name() or staff_user.username,
            'role': staff_user.profile.get_role_display()
        })

    return JsonResponse({
        'staff': staff_data,
        'can_assign': user.profile.role == 'TEAM_LEAD' or user.is_superuser
    })


@login_required
@require_http_methods(["POST"])
def create_project(request):
    """Create a new project (Team Lead and Superuser only)"""
    if request.user.profile.role != 'TEAM_LEAD' and not request.user.is_superuser:
        return JsonResponse({'error': 'Only team leads can create projects'}, status=403)

    try:
        data = json.loads(request.body)

        # Create project
        project = Project.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            start_date=datetime.strptime(data['created'], '%Y-%m-%d').date(),
            created_by=request.user
        )

        # Assign staff members
        if 'staff' in data and data['staff']:
            staff_members = User.objects.filter(id__in=data['staff'])
            project.members.set(staff_members)

        return JsonResponse({
            'success': True,
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created': project.start_date.isoformat(),
                'cost': float(project.total_cost()),
                'staff': [member.id for member in project.members.all()],
                'created_by': project.created_by.id,
                'can_edit': True
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["PUT"])
def update_project(request, project_id):
    """Update an existing project (only creator or superuser)"""
    try:
        project = get_object_or_404(Project, id=project_id)

        # Check permissions: only the creator or superuser can edit
        if not request.user.is_superuser and project.created_by != request.user:
            return JsonResponse({'error': 'You can only edit projects you created'}, status=403)

        # Additional check: must be team lead or superuser
        if request.user.profile.role != 'TEAM_LEAD' and not request.user.is_superuser:
            return JsonResponse({'error': 'Only team leads can update projects'}, status=403)

        data = json.loads(request.body)

        # Update project fields
        project.name = data['name']
        project.description = data.get('description', '')
        project.start_date = datetime.strptime(data['created'], '%Y-%m-%d').date()
        project.save()

        # Update staff members
        if 'staff' in data:
            staff_members = User.objects.filter(id__in=data['staff'])
            project.members.set(staff_members)

        return JsonResponse({
            'success': True,
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created': project.start_date.isoformat(),
                'cost': float(project.total_cost()),
                'staff': [member.id for member in project.members.all()],
                'created_by': project.created_by.id if project.created_by else None,
                'can_edit': True
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_project(request, project_id):
    """Delete a project (only creator or superuser)"""
    try:
        project = get_object_or_404(Project, id=project_id)

        # Check permissions: only the creator or superuser can delete
        if not request.user.is_superuser and project.created_by != request.user:
            return JsonResponse({'error': 'You can only delete projects you created'}, status=403)

        # Additional check: must be team lead or superuser
        if request.user.profile.role != 'TEAM_LEAD' and not request.user.is_superuser:
            return JsonResponse({'error': 'Only team leads can delete projects'}, status=403)

        project.delete()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def tasks_view(request, project_id):
    """Render the tasks page for a specific project"""
    project = get_object_or_404(Project, id=project_id)

    # Staff permission: can only see projects they are assigned to
    if request.user.profile.role == 'STAFF' and request.user not in project.members.all():
        return render(request, 'projects/forbidden.html', status=403)

    return render(request, 'projects/tasks.html', {'project': project})


@login_required
@require_http_methods(["GET"])
def get_project_tasks(request, project_id):
    """Return all tasks for a project based on user permissions"""
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    # Determine accessible tasks
    if user.is_superuser or user.profile.role == 'TEAM_LEAD':
        tasks_qs = project.tasks.all()
        user_role = 'SUPERUSER' if user.is_superuser else 'TEAM_LEAD'
    else:
        tasks_qs = project.tasks.filter(assigned_to=user)
        user_role = 'STAFF'

    tasks_data = []
    for task in tasks_qs:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'time_taken': float(task.time_taken),
            'cost': float(task.cost),
            'completed': task.completed,
            'assigned_to': task.assigned_to.id if task.assigned_to else None,
            'assigned_name': task.assigned_to.get_full_name() if task.assigned_to else '',
        })

    return JsonResponse({'tasks': tasks_data, 'user_role': user_role})


@login_required
@require_http_methods(["POST"])
def create_task(request, project_id):
    """Create a new task (Team Lead or Superuser only)"""
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    if user.profile.role != 'TEAM_LEAD' and not user.is_superuser:
        return JsonResponse({'error': 'Only team leads can create tasks'}, status=403)

    try:
        data = json.loads(request.body)
        assigned_user = None
        if data.get('assigned_to'):
            assigned_user = User.objects.filter(id=data['assigned_to']).first()

        task = Task.objects.create(
            project=project,
            title=data['title'],
            description=data.get('description', ''),
            time_taken=data.get('time_taken', 0),
            cost=data.get('cost', 0),
            assigned_to=assigned_user,
            completed=data.get('completed', False)
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'time_taken': float(task.time_taken),
                'cost': float(task.cost),
                'completed': task.completed,
                'assigned_to': assigned_user.id if assigned_user else None,
                'assigned_name': assigned_user.get_full_name() if assigned_user else ''
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["PUT"])
def update_task(request, project_id, task_id):
    """Update a task (Team Lead/Superuser for any field, Staff can only toggle completed)"""
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    user = request.user

    try:
        data = json.loads(request.body)

        if user.profile.role in ['TEAM_LEAD'] or user.is_superuser:
            # Full edit
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'time_taken' in data:
                task.time_taken = data['time_taken']
            if 'cost' in data:
                task.cost = data['cost']
            if 'assigned_to' in data:
                task.assigned_to = User.objects.filter(id=data['assigned_to']).first() if data['assigned_to'] else None
            if 'completed' in data:
                task.completed = data['completed']
        else:
            # Staff can only update 'completed' for tasks assigned to them
            if task.assigned_to != user:
                return JsonResponse({'error': 'You cannot edit this task'}, status=403)
            if 'completed' in data:
                task.completed = data['completed']

        task.save()

        # Return updated task data
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'time_taken': float(task.time_taken),
                'cost': float(task.cost),
                'completed': task.completed,
                'assigned_to': task.assigned_to.id if task.assigned_to else None,
                'assigned_name': task.assigned_to.get_full_name() if task.assigned_to else ''
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_task(request, project_id, task_id):
    """Delete a task (Team Lead or Superuser only)"""
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    user = request.user

    if user.profile.role != 'TEAM_LEAD' and not user.is_superuser:
        return JsonResponse({'error': 'You cannot delete this task'}, status=403)

    try:
        task.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
