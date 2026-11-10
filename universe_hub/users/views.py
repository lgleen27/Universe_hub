from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum

from .forms import StudentUserCreationForm, StudentUserUpdateForm
from .models import StudentUser, Follow

from posts.models import Post, Project, Like, Comment, ProjectApplication, Notification
from posts.forms import PostForm, ProjectForm, CommentForm


CAREER_LABELS = {
    'arts': 'Artes',
    'business': 'Negocios',
    'design': 'Diseño',
    'engineering': 'Ingeniero',
    'health': 'Salud',
    'law': 'Derecho',
    'other': 'Otros',
}


def register(request):
    if request.method == 'POST':
        form = StudentUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = StudentUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def home(request):
    user = request.user
    post_form = PostForm()
    project_form = ProjectForm()
    comment_form = CommentForm()

    if not user.is_staff:
        university_exists = user.university and user.university.strip()
        major_exists = user.major and user.major.strip()

        if not university_exists or not major_exists:
            return redirect('complete_profile')

    if request.method == 'POST':
        if 'create_post' in request.POST:
            post_form = PostForm(request.POST, request.FILES)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect('home')

        elif 'create_project' in request.POST:
            project_form = ProjectForm(request.POST)
            if project_form.is_valid():
                project = project_form.save(commit=False)
                project.owner = request.user
                project.save()
                return redirect('home')

    posts = Post.objects.select_related('author').prefetch_related(
        'likes',
        'comments__author'
    ).order_by('-created_at')[:20]

    selected_careers = request.GET.getlist('career')

    base_projects = Project.objects.select_related('owner').filter(
        status='open'
    )

    open_projects_list = list(base_projects)
    total_vacancies = sum(p.vacancies for p in open_projects_list)

    raw_careers = sorted({
        career.strip()
        for p in open_projects_list
        if p.target_careers
        for career in p.target_careers.split(',')
        if career.strip()
    })

    available_careers = [
        {
            'value': career,
            'label': CAREER_LABELS.get(career, career.replace('_', ' ').title()),
            'projects_count': sum(
                1 for p in open_projects_list
                if p.target_careers and career in [c.strip() for c in p.target_careers.split(',')]
            ),
            'vacancies': sum(
                p.vacancies for p in open_projects_list
                if p.target_careers and career in [c.strip() for c in p.target_careers.split(',')]
            ),
        }
        for career in raw_careers
    ]

    filtered_projects = base_projects

    if selected_careers:
        career_query = Q()
        for career in selected_careers:
            career_query |= Q(target_careers__icontains=career)

        filtered_projects = filtered_projects.filter(career_query)

    active_vacancies = filtered_projects.aggregate(total=Sum('vacancies'))['total'] or 0
    filtered_projects_count = filtered_projects.count()
    projects = filtered_projects.order_by('-created_at')[:10]

    liked_post_ids = set(
        Like.objects.filter(user=request.user).values_list('post_id', flat=True)
    )

    pending_requests = ProjectApplication.objects.select_related(
        'applicant',
        'project'
    ).filter(
        project__owner=request.user,
        status='pending'
    ).order_by('-created_at')

    my_applications = ProjectApplication.objects.select_related(
        'project',
        'project__owner'
    ).filter(
        applicant=request.user
    ).exclude(
        status='accepted'
    ).order_by('-created_at')

    joined_projects = ProjectApplication.objects.select_related(
        'project',
        'project__owner'
    ).filter(
        applicant=request.user,
        status='accepted'
    ).order_by('-created_at')

    selected_career_labels = [
        CAREER_LABELS.get(career, career.replace('_', ' ').title())
        for career in selected_careers
    ]

    context = {
        'post_form': post_form,
        'project_form': project_form,
        'comment_form': comment_form,
        'posts': posts,
        'available_careers': available_careers,
        'selected_careers': selected_careers,
        'projects': projects,
        'filtered_projects_count': filtered_projects_count,
        'total_vacancies': total_vacancies,
        'active_vacancies': active_vacancies,
        'liked_post_ids': liked_post_ids,
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests.count(),
        'my_applications': my_applications,
        'joined_projects': joined_projects,
        'selected_career_labels': selected_career_labels,
    }

    return render(request, 'home.html', context)


@login_required
def complete_profile(request):
    if request.method == 'POST':
        user = request.user
        user.university = request.POST.get('university')
        user.major = request.POST.get('major')
        user.semester = request.POST.get('semester', 1)
        user.save()
        return redirect('home')

    return render(request, 'users/complete_profile.html')


@login_required
def toggle_like(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(user=request.user, post=post).first()
    liked = False

    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                notification_type='like',
                verb='le gustó tu publicación.',
                post=post
            )

    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': post.likes.count(),
    })


@login_required
def add_comment(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                notification_type='comment',
                verb='comentó en tu publicación.',
                post=post
            )

        return JsonResponse({
            'success': True,
            'comment': {
                'author': comment.author.username,
                'author_url': f'/profile/{comment.author.username}/',
                'content': comment.content,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
            },
            'comments_count': post.comments.count(),
        })

    return JsonResponse({
        'success': False,
        'errors': form.errors,
    }, status=400)


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related('comments__author', 'likes'),
        id=post_id
    )
    comment_form = CommentForm()
    is_liked = post.likes.filter(user=request.user).exists()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'likes_count': post.likes.count(),
        'comments_count': post.comments.count(),
    })


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def profile(request, username=None):
    if username and username != request.user.username:
        user_profile = get_object_or_404(StudentUser, username=username)
        is_own_profile = False
    else:
        user_profile = request.user
        is_own_profile = True

    # --- Lógica para procesar las fotos (POST solo en perfil propio) ---
    if request.method == 'POST' and is_own_profile:
        # Revisamos si viene la foto de portada
        if 'cover_photo' in request.FILES:
            user_profile.cover_photo = request.FILES['cover_photo']
            user_profile.save()
            
        # Revisamos si viene la foto de perfil
        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']
            user_profile.save()
            
        return redirect('profile')

    # --- Lógica para obtener actividad (GET) ---
    
    # 1. Publicaciones hechas por el usuario
    user_posts = Post.objects.filter(author=user_profile).order_by('-created_at')
    
    # 2. Proyectos que el usuario ha creado
    user_projects = Project.objects.filter(owner=user_profile).order_by('-created_at')
    
    # 3. Proyectos donde es colaborador (solicitudes aceptadas)
    joined_projects = ProjectApplication.objects.filter(
        applicant=user_profile, 
        status='accepted'
    ).order_by('-created_at')
    liked_post_ids = set(request.user.likes.values_list('post_id', flat=True))

    # 4. Datos de la red de seguidores (Follow)
    followers_count = user_profile.followers.count()
    following_count = user_profile.following.count()
    is_following = False
    if not is_own_profile:
        is_following = user_profile.followers.filter(follower=request.user).exists()

    context = {
        'user_profile': user_profile,
        'is_own_profile': is_own_profile,
        'user_posts': user_posts,
        'user_projects': user_projects,
        'joined_projects': joined_projects,
        'liked_post_ids': liked_post_ids,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def toggle_follow(request, username):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    target_user = get_object_or_404(StudentUser, username=username)

    if target_user == request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'No puedes seguirte a ti mismo.'
            }, status=400)
        messages.warning(request, 'No puedes seguirte a ti mismo.')
        return redirect('user_profile', username=username)

    follow = Follow.objects.filter(follower=request.user, following=target_user).first()
    if follow:
        follow.delete()
        is_following = False
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        is_following = True
        if target_user != request.user:
            Notification.objects.create(
                recipient=target_user,
                actor=request.user,
                notification_type='follow',
                verb='comenzó a seguirte.'
            )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_following': is_following,
            'followers_count': target_user.followers.count(),
            'following_count': target_user.following.count(),
        })

    return redirect('user_profile', username=username)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        # VITAL: request.FILES debe estar presente
        form = StudentUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado con éxito!')
            return redirect('profile')
        else:
            # Esto imprimirá los errores en tu terminal de VS Code para que sepamos qué falla
            print(form.errors) 
    else:
        form = StudentUserUpdateForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})