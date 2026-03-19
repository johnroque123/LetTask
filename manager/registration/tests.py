from django.test import TestCase
from django.urls import reverse
from registration.models import User
from todo.models import Task


class RegistrationFormTest(TestCase):

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='user1', email='test@gmail.com', password='pass1234!')
        response = self.client.post(reverse('register'), {
            'username': 'user2',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@gmail.com',
            'password': 'pass1234!',
            'password2': 'pass1234!',
        })
        self.assertFormError(response.context['form'], 'email', 'Email already exists.')

    def test_mismatched_passwords_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'user1',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@gmail.com',
            'password': 'pass1234!',
            'password2': 'different1234!',
        })
        self.assertFormError(response.context['form'], None, 'Passwords do not match.')


class TaskOwnershipTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass1234!')
        self.user2 = User.objects.create_user(username='user2', password='pass1234!')
        self.task = Task.objects.create(
            user=self.user1,
            title='User1 private task',
            priority='high',
        )

    def test_user_cannot_edit_another_users_task(self):
        self.client.login(username='user2', password='pass1234!')
        response = self.client.get(reverse('update_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_task(self):
        self.client.login(username='user2', password='pass1234!')
        response = self.client.post(reverse('delete_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_dashboard_only_shows_own_tasks(self):
        self.client.login(username='user2', password='pass1234!')
        response = self.client.get(reverse('dashboard'))
        tasks_in_context = list(response.context['pending_tasks'])
        self.assertNotIn(self.task, tasks_in_context)