from posts.models import ProjectApplication, Notification


def notifications_processor(request):
    if not request.user.is_authenticated:
        return {
            'notifications_list': [],
            'unread_notifications_count': 0,
            'pending_requests': [],
            'pending_requests_count': 0,
        }

    try:
        pending_requests = list(
            ProjectApplication.objects.select_related('applicant', 'project')
            .filter(project__owner=request.user, status='pending')
            .order_by('-created_at')
        )
    except Exception:
        pending_requests = []

    try:
        notifications_list = list(
            Notification.objects.select_related('actor', 'post', 'project', 'application')
            .filter(recipient=request.user)
            .order_by('-created_at')[:20]
        )
        unread_notifications = sum(1 for n in notifications_list if not n.is_read)
    except Exception:
        notifications_list = []
        unread_notifications = 0

    total_unread = len(pending_requests) + unread_notifications

    return {
        'notifications_list': notifications_list,
        'unread_notifications_count': total_unread,
        'pending_requests': pending_requests,
        'pending_requests_count': len(pending_requests),
    }
