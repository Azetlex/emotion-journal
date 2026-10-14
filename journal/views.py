# Python standard library
import base64
import io
import json
import re
from collections import Counter

# Third-party libraries
import matplotlib.pyplot as plt

# Django
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.utils.html import escape, format_html
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

# Local application
from .models import Entry, Topic

class LockedView(LoginRequiredMixin):
    login_url = "/login/"

@login_required(login_url='/login/')
def topic_list(request):
    # 🔥 MODIFICAT - Doar topicurile userului logat
    topics = Topic.objects.filter(user=request.user)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search_query')

    if start_date:
        topics = topics.filter(created_at__gte=start_date)
    if end_date:
        topics = topics.filter(created_at__lte=end_date)
    
    if search_query:
     entries = Entry.objects.filter(
        topic__user=request.user
    ).filter(
        Q(title__icontains=search_query) |
        Q(content__icontains=search_query)
     )
     if entries.exists():
            first_entry = entries.first()
            return redirect(reverse('entry_detail', args=[first_entry.id]) + f"?highlight={search_query}")

    return render(request, 'journal/index.html', {'topics': topics})

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title']

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['title', 'content', 'emotion']

@login_required(login_url='/login/')
def topic_create(request):
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)  # 🔥 MODIFICAT
            topic.user = request.user  # 🔥 ADAUGAT
            topic.save()  # 🔥 ADAUGAT
            return redirect('index')
    else:
        form = TopicForm()

    return render(request, 'journal/topic_create.html', {'form': form})

@login_required(login_url='/login/')
def entry_create(request, topic_id):
    # 🔥 MODIFICAT - Verifică că topicul aparține userului
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        emotion = request.POST['emotion']
        Entry.objects.create(topic=topic, title=title, content=content, emotion=emotion)
        return redirect('topic_detail', topic_id=topic_id)
    return render(request, 'journal/entry_create.html', {'topic': topic})

@login_required(login_url='/login/')
def topic_detail(request, topic_id):
    # 🔥 MODIFICAT - Verifică că topicul aparține userului
    topic = get_object_or_404(Topic, pk=topic_id, user=request.user)
    entries = Entry.objects.filter(topic=topic_id)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search_query')

    if start_date:
        start_date = parse_date(start_date)
        entries = entries.filter(created_at__gte=start_date)
    if end_date:
        end_date = parse_date(end_date)
        entries = entries.filter(created_at__lte=end_date)
    if search_query:
        entries = entries.filter(title__icontains=search_query)


    emotion_counts = {}
    for entry in entries:
        emotion = entry.emotion
        if emotion in emotion_counts:
            emotion_counts[emotion] += 1
        else:
            emotion_counts[emotion] = 1


    emotion_counts_json = json.dumps(emotion_counts)

    return render(request, 'journal/topic_detail.html', {
        'topic': topic,
        'entries': entries,
        'emotion_counts': emotion_counts_json
    })

@login_required(login_url='/login/')
def edit_entry(request, entry_id):
    # 🔥 MODIFICAT - Verifică că entry-ul aparține userului
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
    emotions = Entry._meta.get_field('emotion').choices
    return render(request, 'journal/entry_form.html', {'entry': entry, 'emotions': emotions})

class EntryUpdateView(LockedView, SuccessMessageMixin, UpdateView):
    model = Entry
    fields = ["title", "content", "emotion"]
    success_message = "Your entry was updated!"

    def get_queryset(self):
     return Entry.objects.filter(topic__user=self.request.user)

    def get_success_url(self):
        return reverse_lazy("entry_detail", kwargs={"pk": self.object.pk})

@login_required(login_url='/login/')
def delete_entry(request):
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        # 🔥 MODIFICAT - Verifică că entry-ul aparține userului
        entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
        entry.delete()
        return redirect('topic_detail', topic_id=entry.topic.id)
        return HttpResponse(status=405)

class EntryListView(ListView):
    model = Entry
    template_name = 'entry_list.html'
    context_object_name = 'entry_list'

    def topic_detail(request, topic_id):
        request.session['topic_id'] = topic_id

    def get_queryset(self):
        topic = get_object_or_404(Topic, pk=self.kwargs['pk'])
        return Entry.objects.filter(topic=topic).order_by("-date_created")

class EntryDetailView(LockedView, DetailView):
    model = Entry
    template_name = 'journal/entry_detail.html'  

    def get_queryset(self):
     return Entry.objects.filter(topic__user=self.request.user)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        highlight = self.request.GET.get('highlight')

        if highlight:
            entry = self.get_object()

            parts = re.split(
                f"({re.escape(highlight)})",
                entry.content,
                flags=re.IGNORECASE
            )

            highlighted_content = ""

            for part in parts:
                if part.lower() == highlight.lower():
                    highlighted_content += format_html(
                        '<span class="highlight">{}</span>',
                        part
                    )
                else:
                    highlighted_content += escape(part)

            entry.content = highlighted_content
            context['entry'] = entry

        return context

        

@login_required(login_url='/login/')
def entry_statistics(request):
    entries = Entry.objects.filter(topic__user=request.user)
    emotions = [entry.emotion for entry in entries]
    emotion_counts = Counter(emotions)

    chart_image = None

    if emotion_counts:
        fig, ax = plt.subplots(figsize=(8, 8))

        ax.pie(
            emotion_counts.values(),
            labels=emotion_counts.keys(),
            autopct='%1.1f%%',
            startangle=140
        )

        ax.set_title('Emotion Distribution in Entries')
        ax.axis('equal')

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)

        buffer.seek(0)
        chart_image = base64.b64encode(
            buffer.getvalue()
        ).decode('utf-8')

        buffer.close()

    return render(
        request,
        'journal/entry_statistics.html',
        {'chart_image': chart_image}
    )


@login_required(login_url='/login/')
def delete_topic(request):
    if request.method == 'POST':
        topic_id = request.POST.get('topic_id')
        # 🔥 MODIFICAT - Verifică că topicul aparține userului
        topic = get_object_or_404(Topic, id=topic_id, user=request.user)
        topic.delete()
        return redirect('index')
    return HttpResponse(status=405)

class LoginView(TemplateView):
    template_name = 'login.html'

    def get(self, request):
        return self.render_to_response({})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return self.render_to_response({'error': 'Invalid username or password.'})

class SignUpView(TemplateView):
    template_name = 'signup.html'

    def get(self, request):
        return self.render_to_response({})

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            return self.render_to_response({'error': 'Passwords do not match.'})
        try:
         validate_password(password1)
        except ValidationError as error:
         return self.render_to_response({
        'error': ' '.join(error.messages)
    })

        if User.objects.filter(username=username).exists():
            return self.render_to_response({'error': 'Username already exists.'})
        if User.objects.filter(email=email).exists():
            return self.render_to_response({'error': 'Email already in use.'})

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect('login')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def entry_content(request, entry_id):
    # 🔥 MODIFICAT - Verifică că entry-ul aparține userului
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
    return JsonResponse({'content': entry.content})
