from django.contrib import admin
from .models import Post, Project, Comment, Like, ProjectApplication, Notification


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_at', 'is_project']
    list_filter = ['is_project', 'created_at']
    search_fields = ['content', 'author__username']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'summary']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_at']
    list_filter = ['created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']


@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'project', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'actor', 'notification_type', 'verb', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
