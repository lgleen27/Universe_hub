from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from posts.models import Project, ProjectApplication, Notification


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project.objects.select_related('owner'), id=project_id)

    existing_application = ProjectApplication.objects.filter(
        project=project,
        applicant=request.user
    ).first()

    is_owner = project.owner == request.user

    context = {
        'project': project,
        'existing_application': existing_application,
        'is_owner': is_owner,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def apply_to_project(request, project_id):
    if request.method != 'POST':
        return redirect('project_detail', project_id=project_id)

    project = get_object_or_404(Project, id=project_id)

    if project.owner == request.user:
        messages.warning(request, 'No puedes solicitar entrar a tu propio proyecto.')
        return redirect('project_detail', project_id=project.id)

    application, created = ProjectApplication.objects.get_or_create(
        project=project,
        applicant=request.user,
        defaults={'status': 'pending'}
    )

    if created:
        if project.owner != request.user:
            Notification.objects.create(
                recipient=project.owner,
                actor=request.user,
                notification_type='project_application',
                verb=f'solicitó unirse a tu proyecto "{project.title}".',
                project=project,
                application=application
            )
        messages.success(request, 'Tu solicitud fue enviada correctamente.')
    else:
        if application.status == 'pending':
            messages.info(request, 'Ya habías enviado una solicitud a este proyecto.')
        elif application.status == 'accepted':
            messages.success(request, 'Ya formas parte de este proyecto.')
        elif application.status == 'rejected':
            messages.warning(request, 'Tu solicitud anterior fue rechazada.')

    return redirect('project_detail', project_id=project.id)


@login_required
def accept_application(request, application_id):
    if request.method != 'POST':
        return redirect('home')

    application = get_object_or_404(
        ProjectApplication.objects.select_related('project', 'applicant'),
        id=application_id
    )

    if application.project.owner != request.user:
        messages.error(request, 'No tienes permiso para aceptar esta solicitud.')
        return redirect('home')

    if application.status != 'pending':
        messages.info(request, 'Esta solicitud ya fue procesada.')
        return redirect('home')

    project = application.project

    if project.vacancies <= 0:
        project.status = 'closed'
        project.save(update_fields=['status'])
        messages.warning(request, 'Este proyecto ya no tiene vacantes disponibles.')
        return redirect('home')

    application.status = 'accepted'
    application.save(update_fields=['status'])

    project.vacancies -= 1

    if project.vacancies <= 0:
        project.vacancies = 0
        project.status = 'closed'
        project.save(update_fields=['vacancies', 'status'])
    else:
        project.save(update_fields=['vacancies'])

    Notification.objects.create(
        recipient=application.applicant,
        actor=request.user,
        notification_type='project_application',
        verb=f'aceptó tu solicitud en "{project.title}".',
        project=project,
        application=application
    )

    messages.success(
        request,
        f'{application.applicant.username} fue aceptado en "{project.title}".'
    )
    return redirect('home')


@login_required
def reject_application(request, application_id):
    if request.method != 'POST':
        return redirect('home')

    application = get_object_or_404(
        ProjectApplication.objects.select_related('project', 'applicant'),
        id=application_id
    )

    if application.project.owner != request.user:
        messages.error(request, 'No tienes permiso para rechazar esta solicitud.')
        return redirect('home')

    if application.status != 'pending':
        messages.info(request, 'Esta solicitud ya fue procesada.')
        return redirect('home')

    application.status = 'rejected'
    application.save(update_fields=['status'])

    Notification.objects.create(
        recipient=application.applicant,
        actor=request.user,
        notification_type='project_application',
        verb=f'rechazó tu solicitud en "{application.project.title}".',
        project=application.project,
        application=application
    )

    messages.warning(
        request,
        f'{application.applicant.username} fue rechazado en "{application.project.title}".'
    )
    return redirect('home')
