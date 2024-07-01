import json
import os

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from pytube import YouTube

from ai_blog_app import settings

from .models import BlogPost


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            youtube_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)

        # get youtube title
        title = _youtube_title(link=youtube_link)

        # get transcript
        transcription = _get_transcription(link=youtube_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcription'}, status=500)

        # use OpenAI to generate the blog
        blog_content = _generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'}, status=500)

        # save blog article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=youtube_link,
            generated_contend=blog_content,
        )
        new_blog_article.save()

        # return blog article as a response
        return JsonResponse({'content': blog_content}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def _youtube_title(link: str) -> str:
    youtube = YouTube(url=link)
    return youtube.title


def _download_audio(link: str):
    youtube = YouTube(url=link)
    if video := youtube.streams.filter(only_audio=True).first():
        out_file = video.download(output_path=settings.MEDIA_ROOT)
        base, _ = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
        return new_file


def _get_transcription(link: str):
    audio_file_path = _download_audio(link)
    client = OpenAI()
    with open(audio_file_path, 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcription.text


def _generate_blog_from_transcription(transcription: str):
    client = OpenAI()
    completion = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following transcription that belongs to a youtube Video and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points.",
            },
            {"role": "user", "content": transcription},
        ],
    )
    return completion.choices[0].message.content


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeat_password = request.POST['repeatPassword']

        if password == repeat_password:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except Exception:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message': error_message})
    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
