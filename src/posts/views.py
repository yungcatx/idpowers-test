from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Prefetch
from django.http import HttpResponseForbidden, Http404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import FormMixin

from posts.forms import PostForm, CommentForm, MarkForm
from posts.models import Post, Category, Mark, Comment


# Create your views here.

class AllPostsListView(generic.ListView):
    template_name = 'posts.html'

    def get_queryset(self):
        queryset = Post.objects.all().prefetch_related(
            Prefetch('author'),
            Prefetch('category')
        )

        keywords = self.request.GET.get('q')
        sort = self.request.GET.get('sort')

        if keywords:
            print(keywords)
            query = SearchQuery(keywords)
            title_vector = SearchVector('title', weight='A')
            content_vector = SearchVector('content', weight='B')
            vectors = title_vector + content_vector
            queryset = queryset.annotate(search=vectors).filter(search=query)
            queryset = queryset.annotate(rank=SearchRank(vectors, query)).order_by('-rank')

        if sort:
            print(sort)
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(AllPostsListView, self).get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        context['title'] = 'Публикации пользователей'
        return context


class MyPostsListView(LoginRequiredMixin, generic.ListView):
    template_name = 'posts.html'
    login_url = reverse_lazy('users:login')

    def get_queryset(self):
        queryset = Post.objects.prefetch_related(
            Prefetch('author')
        ).filter(author=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MyPostsListView, self).get_context_data(**kwargs)
        context['title'] = 'Мои публикации'
        return context


class PostsByPk(generic.ListView):
    template_name = 'posts.html'

    def get_queryset(self, **kwargs):
        author_pk = self.kwargs.get('pk')
        queryset = Post.objects.filter(author_id__exact=author_pk)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostsByPk, self).get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        return context


class PostsByCategory(generic.ListView):
    template_name = 'posts.html'

    def get_queryset(self):
        title = self.kwargs['title']
        queryset = Post.objects.prefetch_related(
            Prefetch('category')
        ).filter(category__title__exact=title)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        title = self.kwargs['title']
        context = super(PostsByCategory, self).get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        context['title'] = f'Публикации в категории {title}'
        return context


class PostDetailView(FormMixin, generic.DetailView):
    template_name = 'post_detail.html'
    form_class = CommentForm
    second_form_class = MarkForm

    def get_success_url(self):
        return reverse_lazy("posts:detail-post", args={self.get_object().pk})

    def get_queryset(self):
        marks_queryset = Mark.objects.filter(sender=self.request.user)
        queryset = Post.objects.prefetch_related(
            Prefetch('comments'),
            Prefetch('marks', queryset=marks_queryset)
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data()
        context['obj'] = self.get_object(self.get_queryset())
        if self.request.user.is_authenticated:
            context['form'] = CommentForm(initial={"sender": self.request.user, "post": self.get_object()})
            context['mark_form'] = MarkForm(initial={"sender": self.request.user, "post": self.get_object()})
        return context

    def post(self, request, *args, **kwargs):
        posting = self.get_object()
        print(request.POST)
        if request.user == posting.author:
            return HttpResponseForbidden()

        if 'form1' in request.POST:
            form = self.form_class(request.POST)
        else:
            form = self.second_form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        print(form)
        form.save()
        return super(PostDetailView, self).form_valid(form)


class PostCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = PostForm
    model = Post
    template_name = 'form.html'
    success_url = reverse_lazy('posts:my-posts')

    def get_context_data(self, **kwargs):
        context = super(PostCreateView, self).get_context_data()
        context['form'] = self.form_class()
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(PostCreateView, self).form_valid(form)


class PostUpdateView(LoginRequiredMixin, generic.CreateView):
    model = Post
    fields = ['title', 'summary', 'content']
    template_name = 'form.html'

    def get_success_url(self):
        return reverse_lazy('posts:post-detail', args={self.object.pk})

    def get_object(self, queryset=None):
        obj = super(PostUpdateView, self).get_object()
        if not obj.author == self.request:
            raise Http404
        return obj


class PostDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Post
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('posts:my-posts')

    def get_object(self, queryset=None):
        obj = super(PostDeleteView, self).get_object()
        if not obj.author == self.request.user:
            raise Http404
        return obj


class CategoryListView(generic.ListView):
    template_name = 'main.html'

    def get_queryset(self):
        queryset = Category.objects.all()
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        return context
