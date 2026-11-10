from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(max_length=1000, blank=True)
    image = models.ImageField(
        upload_to='posts/images/',
        blank=True,
        null=True,
        verbose_name='Imagen'
    )
    attachment = models.FileField(
        upload_to='posts/files/',
        blank=True,
        null=True,
        verbose_name='Archivo adjunto',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'txt', 'doc', 'docx']
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_project = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post #{self.id} by {self.author}"

    @property
    def attachment_name(self):
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return ''

    @property
    def attachment_extension(self):
        if self.attachment:
            return self.attachment.name.split('.')[-1].lower()
        return ''


class Project(models.Model):
    STATUS_CHOICES = [
        ('open', 'Abierto a colaboración'),
        ('in_progress', 'En desarrollo'),
        ('closed', 'Cerrado'),
    ]

    PROJECT_TYPES = [
        ('class', 'Proyecto de clase'),
        ('thesis', 'Tesis o Tesina'),
        ('hackathon', 'Concurso o Hackathon'),
        ('startup', 'Emprendimiento propio'),
    ]

    PROJECT_STAGES = [
        ('idea', 'Solo es una idea (Fase 0)'),
        ('planning', 'En planeación / Diseño (Fase 1)'),
        ('prototype', 'Prototipo iniciado (Fase 2)'),
        ('active', 'En desarrollo activo (Fase 3)'),
    ]

    WORK_MODES = [
        ('remote', '100% Remoto'),
        ('onsite', 'Presencial (En campus)'),
        ('hybrid', 'Híbrido'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300)
    description = models.TextField()
    problem_and_goal = models.TextField(blank=True, default='')
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    stage = models.CharField(max_length=20, choices=PROJECT_STAGES)
    vacancies = models.PositiveIntegerField(default=1)
    target_careers = models.TextField(blank=True)
    required_skills = models.TextField(
        help_text='Lista de habilidades requeridas separadas por comas'
    )
    work_mode = models.CharField(max_length=20, choices=WORK_MODES)
    application_deadline = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    incentive = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True,
        blank=True
    )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.post or self.project
        return f"Comment by {self.author} on {target}"


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} ♥ Post #{self.post_id}"
    
class ProjectApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
    ]

    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_applications'
    )
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'applicant')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.applicant.username} -> {self.project.title} ({self.status})'


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow', 'Nuevo seguidor'),
        ('like', 'Me gusta'),
        ('comment', 'Comentario'),
        ('project_application', 'Solicitud de proyecto'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    verb = models.CharField(max_length=255)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    application = models.ForeignKey(
        ProjectApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor} -> {self.recipient}: {self.verb}"