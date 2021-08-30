from datetime import datetime
from django.http import request
from django.utils import timezone
from django.utils.decorators import method_decorator

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import query
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from os import truncate
from rango.bing_search import run_query
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.models import Category, Page, UserProfile

from rango.helpers import get_category_list


def index(request):

    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = pages_list

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    response = render(request, 'rango/index.html', context=context_dict)

    return response


class IndexView(View):
    """
    This class returns the home page of Rango.
    """

    def get(self, request):
        category_list = Category.objects.order_by('-likes')[:5]
        pages_list = Page.objects.order_by('-views')[:5]
        context_dict = {}
        context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
        context_dict['categories'] = category_list
        context_dict['pages'] = pages_list

        visitor_cookie_handler(request)
        context_dict['visits'] = request.session['visits']

        response = render(request, 'rango/index.html', context=context_dict)

        return response


class AboutView(View):
    """
    This class returns the about page of Rango.
    """

    def get(self, request):
        context_dict = {'boldmessage':
                        'This tutorial has been put together by Jino!'}
        visitor_cookie_handler(request)
        context_dict['visits'] = request.session['visits']
        return render(request, 'rango/about.html', context_dict)


class ShowCategoryView(View):
    """
    This class returns categories of Rango and its pages.
    """
    def get_context(self, category_name_slug):
        try:
            context_dict = {}
            category = Category.objects.get(slug=category_name_slug)
            pages = Page.objects.filter(category=category).order_by('-views')
            context_dict['pages'] = pages
            context_dict['category'] = category
        except Category.DoesNotExist:
            context_dict['category'] = None
            context_dict['pages'] = None
        return context_dict

    def get(self, request, category_name_slug):
        context_dict = self.get_context(category_name_slug)
        return render(request, 'rango/category.html', context_dict)

    @method_decorator(login_required)
    def post(self, request, category_name_slug):
        result_list = []
        context_dict = self.get_context(category_name_slug)
        
        query = request.POST['query'].strip()
        context_dict["query"] = query
        if query:
            result_list = run_query(query)
            context_dict["result_list"] = result_list
        return render(request, 'rango/category.html', context_dict)
    



class AddCategoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = CategoryForm()
        return render(request, 'rango/add_category.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print(form.errors)
        return render(request, 'rango/add_category.html', {'form': form})


def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            cat = form.save(commit=True)
            print(cat, cat.slug)
            return index(request)
        else:
            print(form.errors)
    return render(request, 'rango/add_category.html', {'form': form})


class AddPageView(View):
    @method_decorator(login_required)
    def get(self, request, category_name_slug):
        try:
            category = Category.objects.get(slug=category_name_slug)
            form = PageForm()
            context_dict = {'form': form, 'category': category}
        except Category.DoesNotExist:
            category = None
        return render(request, 'rango/add_page.html', context_dict)
    
    @method_decorator(login_required)
    def post(self, request, category_name_slug):
        print(category_name_slug)
        category = Category.objects.get(slug=category_name_slug)
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.last_visit = timezone.now()
                page.save()

                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                category_name_slug}))
            else:
                print(form.errors)

        context_dict = {'form': form, 'category': category}
        return render(request, 'rango/add_page.html', context_dict)


class RestrictedView(View):
    @method_decorator(login_required)
    def get(self, request):
        context_dict = {}
        context_dict["message"] = "Since you're logged in, you can see this text!"
        return render(request, 'rango/restricted.html', context_dict)


def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit',
                                               str(datetime.now()))

    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits


# def search(request):
#     result_list = []
#     context_dict = {}
#     if request.method == 'POST':
#         query = request.POST['query'].strip()
#         context_dict["query"] = query
#         if query:
#             result_list = run_query(query)
#             context_dict["result_list"] = result_list
#     return render(request, 'rango/search.html', context_dict )

class GoToUrlView(View):
    def get(self, request):
        page_id = None
        page_id = request.GET.get('page_id')
        try:
            page = Page.objects.get(id=page_id)
            page.views = page.views + 1
            page.last_visit = timezone.now()
            page.save()
            return redirect(page.url)
        except:
            return redirect(reverse('rango:index'))


@login_required
def register_profile(request):
    form = UserProfileForm()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect('rango:index')
        else:
            print(form.errors)
    context_dict = {'form': form}
    return render(request, 'rango/profile_registration.html', context_dict)


class ShowProfileView(View):
    def get(self, request):
        context_dict = {}
        userprofile_id = None
        try:
            userprofile = UserProfile.objects.get(id=userprofile_id)
            context_dict['userprofile'] = userprofile
        except UserProfile.DoesNotExist:
            context_dict['userprofile'] = None
        return render(request, 'rango/profile.html', context_dict)


class ProfileView(View):
    def get_user_details(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        userprofile = UserProfile.objects.get_or_create(user=user)[0]
        form = UserProfileForm({'website': userprofile.website,
                                'picture': userprofile.picture})
        
        return (user, userprofile, form)

    @method_decorator(login_required)
    def get(self, request, username):
        try:
            (user, userprofile, form) = self.get_user_details(username)
        except TypeError:
            return redirect('rango:index')
        
        context_dict = {'userprofile': userprofile,
                        'selecteduser': user,
                        'form': form}
        return render(request, 'rango/profile.html', context_dict)
    
    @method_decorator(login_required)
    def post(self, request, username):
        try:
            (user, userprofile, form) = self.get_user_details(username)
        except TypeError:
            return redirect('rango:index')
        
        form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        if form.is_valid():
            form.save(commit=True)
            return redirect('rango:profile', user.username)
        else:
            print(form.errors)
        
        context_dict = {'userprofile': userprofile,
                       'selecteduser': user,
                       'form': form}
        return render(request, 'rango/profile.html', context_dict)


class ListProfilesView(View):
    @method_decorator(login_required)
    def get(self, request):
        profiles = UserProfile.objects.all()
        return render(request, 'rango/list_profiles.html',
                        {'userprofile_list' : profiles})

class LikeCategoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        category_id = request.GET['category_id']

        try:
            category = Category.objects.get(id=int(category_id))
        except Category.DoesNotExist:
            return HttpResponse(-1)
        except ValueError:
            return HttpResponse(-1)

        category.likes = category.likes + 1
        category.save()

        return HttpResponse(category.likes)
        

class CategorySuggestionView(View):
    def get(self, request):
        suggestion = request.GET['suggestion']
        category_list = get_category_list(max_results=8, 
                                          starts_with=suggestion)

        if len(category_list) == 0:
            category_list = Category.objects.order_by('-likes')
        
        return render(request, 'rango/categories.html',
                       {'categories': category_list})


class AddSearchedPageView(View):
    @method_decorator(login_required)
    def get(self, request):
        category_id = request.GET['category_id']
        title = request.GET['title']
        url = request.GET['url']

        try:
            category = Category.objects.get(id=int(category_id))
        except Category.DoesNotExist:
            return HttpResponse('Error - category not found.')
        except ValueError:
            return HttpResponse('Error - bad category ID.')

        p = Page.objects.get_or_create(category=category,
                                        title=title,
                                        url=url)
        pages = Page.objects.filter(category=category).order_by('-views')
        print(pages)
        return render(request, 'rango/page_listing.html', {'pages': pages})    
