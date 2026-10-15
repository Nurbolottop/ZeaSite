from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .forms import ContactForm


@require_POST
@csrf_protect
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


def brief_page(request):
    """Страница брифа: GET — форма по шагам, POST — сохранение (fetch → JSON,
    без JS — обычная отправка и страница «Спасибо»)."""
    from django.shortcuts import render
    from apps.base.views import _site_context
    from .brief import STEPS
    from .forms import BriefForm

    wants_json = request.headers.get('x-requested-with') == 'fetch'
    sent = False
    form = BriefForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if wants_json:
                return JsonResponse({'ok': True})
            sent = True
        elif wants_json:
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    from django.utils.translation import gettext as _
    context = _site_context(request, url_name='site_brief',
                            meta_title=_('Бриф на разработку'),
                            meta_description=_('Расскажите о продукте, который хотите создать: мы изучим задачу и предложим решение.'))
    steps = [{**step, 'bound': [(f, form[f['key']]) for f in step['fields']]} for step in STEPS]
    context.update({'form': form, 'steps': steps, 'sent': sent})
    return render(request, 'site/brief.html', context)
