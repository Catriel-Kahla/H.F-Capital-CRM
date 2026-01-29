from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.management import call_command
from django.contrib import messages
from django.shortcuts import redirect

@require_POST
def recalculate_scores(request):
    call_command('recalculate_scores')
    messages.success(request, 'Company and lead scores recalculated successfully.')
    return redirect(request.POST.get('next', '/'))
