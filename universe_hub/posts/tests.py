from django.test import TestCase, Client
from django.urls import reverse
from users.models import StudentUser
from posts.models import Post, Like, Comment


class PostInteractionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = StudentUser.objects.create_user(
            username='autor_post',
            email='autor@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Ingeniería en Computación',
            semester=4,
        )
        self.post = Post.objects.create(
            author=self.user,
            content='Publicación de prueba para verificar likes y comentarios.',
        )

    def test_toggle_like(self):
        self.client.login(username='autor_post', password='Password123!')
        url = reverse('toggle_like', kwargs={'post_id': self.post.id})

        # 1. Dar like
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())

        # 2. Quitar like
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['liked'])
        self.assertEqual(data['likes_count'], 0)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_add_comment(self):
        self.client.login(username='autor_post', password='Password123!')
        url = reverse('add_comment', kwargs={'post_id': self.post.id})
        response = self.client.post(url, {'content': 'Excelente post de prueba.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['comment']['author'], 'autor_post')
        self.assertEqual(data['comment']['author_url'], '/profile/autor_post/')
        self.assertEqual(data['comment']['content'], 'Excelente post de prueba.')
        self.assertEqual(data['comments_count'], 1)
        self.assertTrue(Comment.objects.filter(post=self.post, author=self.user).exists())

    def test_notification_on_like_and_comment_from_other_user(self):
        other_user = StudentUser.objects.create_user(
            username='lector_post',
            email='lector@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Derecho',
            semester=2,
        )
        self.client.login(username='lector_post', password='Password123!')

        # Like
        like_url = reverse('toggle_like', kwargs={'post_id': self.post.id})
        self.client.post(like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check notification
        from posts.models import Notification
        self.assertTrue(Notification.objects.filter(
            recipient=self.user,
            actor=other_user,
            notification_type='like',
            post=self.post
        ).exists())

        # Comment
        comment_url = reverse('add_comment', kwargs={'post_id': self.post.id})
        self.client.post(comment_url, {'content': 'Comentario de otro usuario'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertTrue(Notification.objects.filter(
            recipient=self.user,
            actor=other_user,
            notification_type='comment',
            post=self.post
        ).exists())

    def test_post_detail_view(self):
        self.client.login(username='autor_post', password='Password123!')
        Comment.objects.create(author=self.user, post=self.post, content='Comentario uno')
        Comment.objects.create(author=self.user, post=self.post, content='Comentario dos')
        Comment.objects.create(author=self.user, post=self.post, content='Comentario tres')

        detail_url = reverse('post_detail', kwargs={'post_id': self.post.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comentario uno')
        self.assertContains(response, 'Comentario dos')
        self.assertContains(response, 'Comentario tres')
        self.assertContains(response, 'Todos los comentarios (3)')

    def test_mark_notifications_read(self):
        other_user = StudentUser.objects.create_user(
            username='amigo_post',
            email='amigo@udg.mx',
            password='Password123!',
        )
        from posts.models import Notification
        Notification.objects.create(
            recipient=self.user,
            actor=other_user,
            notification_type='like',
            verb='le gustó tu publicación.',
            post=self.post,
            is_read=False
        )

        self.client.login(username='autor_post', password='Password123!')
        read_url = reverse('mark_notifications_read')
        response = self.client.post(read_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Notification.objects.filter(recipient=self.user, is_read=False).exists())
