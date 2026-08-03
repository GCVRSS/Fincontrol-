from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from finances.services import generate_pdf_report


class Command(BaseCommand):
    help = 'Envia o relatório financeiro mensal por e-mail para todos os usuários'

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')

        total_enviados = 0

        for user in users:
            pdf_buffer = generate_pdf_report(user)

            email = EmailMessage(
                subject='Seu relatório financeiro mensal - FinControl',
                body=f'Olá, {user.username}!\n\nSegue em anexo o seu relatório financeiro deste mês.\n\nEquipe FinControl.',
                from_email='noreply@fincontrol.com',
                to=[user.email],
            )
            email.attach('relatorio_fincontrol.pdf', pdf_buffer.read(), 'application/pdf')
            email.send(fail_silently=False)

            total_enviados += 1
            self.stdout.write(self.style.SUCCESS(f'Relatório enviado para {user.username} ({user.email})'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal de relatórios enviados: {total_enviados}'))