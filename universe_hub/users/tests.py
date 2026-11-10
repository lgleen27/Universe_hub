from django.test import TestCase, Client
from django.urls import reverse
from users.models import StudentUser, Follow


class UserProfileAndFollowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = StudentUser.objects.create_user(
            username='estudiante1',
            email='est1@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Ingeniería en Computación',
            semester=5,
        )
        self.user2 = StudentUser.objects.create_user(
            username='estudiante2',
            email='est2@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Derecho',
            semester=3,
        )

    def test_own_profile_view(self):
        self.client.login(username='estudiante1', password='Password123!')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_own_profile'])
        self.assertEqual(response.context['user_profile'], self.user1)

    def test_other_user_profile_view(self):
        self.client.login(username='estudiante1', password='Password123!')
        response = self.client.get(reverse('user_profile', kwargs={'username': self.user2.username}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_own_profile'])
        self.assertEqual(response.context['user_profile'], self.user2)

    def test_toggle_follow_flow(self):
        self.client.login(username='estudiante1', password='Password123!')
        url = reverse('toggle_follow', kwargs={'username': self.user2.username})

        # 1. Seguir
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_following'])
        self.assertEqual(data['followers_count'], 1)
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

        # 2. Dejar de seguir
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_following'])
        self.assertEqual(data['followers_count'], 0)
        self.assertFalse(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

    def test_cannot_follow_self(self):
        self.client.login(username='estudiante1', password='Password123!')
        url = reverse('toggle_follow', kwargs={'username': self.user1.username})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_toggle_follow_fallback_redirect(self):
        self.client.login(username='estudiante1', password='Password123!')
        url = reverse('toggle_follow', kwargs={'username': self.user2.username})
        # Petición tradicional sin header XMLHttpRequest
        response = self.client.post(url)
        self.assertRedirects(response, reverse('user_profile', kwargs={'username': self.user2.username}))
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

    def test_home_projects_and_career_filter(self):
        from posts.models import Project
        Project.objects.create(
            owner=self.user1,
            title='Proyecto Alfa',
            problem_and_goal='Meta del proyecto alfa',
            project_type='research',
            stage='idea',
            work_mode='remote',
            required_skills='Python, Django',
            target_careers='engineering',
            vacancies=4,
            status='open'
        )
        self.client.login(username='estudiante1', password='Password123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtered_projects_count'], 1)
        self.assertEqual(response.context['active_vacancies'], 4)
        career_item = next((c for c in response.context['available_careers'] if c['value'] == 'engineering'), None)
        self.assertIsNotNone(career_item)
        self.assertEqual(career_item['projects_count'], 1)
        self.assertEqual(career_item['vacancies'], 4)
        self.assertContains(response, '1 proyecto · 4 vacantes disponibles')
        self.assertContains(response, '1 proyecto (4 vac.)')
