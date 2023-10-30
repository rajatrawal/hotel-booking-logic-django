from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from django.contrib.auth.models import User
from . models import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime


def check_booking(uid, room_count, start_date, end_date):
    qs = HotelBooking.objects.filter(hotel__uid=uid)
    # qs1 = qs.filter(
    #     start_date__gte=start_date,
    #     end_date__lte=end_date,
    # )
    # qs2 = qs.filter(
    #     start_date__lte=start_date,
    #     end_date__gte=end_date,
    # )

    qs = qs.filter(
        Q(start_date__gte=start_date,
          end_date__lte=end_date)
        | Q(start_date__lte=start_date,
            end_date__gte=end_date)
    )
    # qs = qs1|qs2

    if len(qs) >= room_count:
        return False
    return True


def index(request):
    amenities = Amenities.objects.all()
    hotels = Hotel.objects.all()
    total_hotels = len(hotels)  
    selected_amenities = request.GET.getlist('selectAmenity')
    sort_by = request.GET.get('sortSelect')
    search = request.GET.get('searchInput')
    startdate = request.GET.get('startDate')
    enddate = request.GET.get('endDate')
    price = request.GET.get('price')

    if selected_amenities != []:
        hotels = hotels.filter(
            amenities__amenity_name__in=selected_amenities).distinct()
    if search:

        hotels = hotels.filter(Q(hotel_name__icontains=search)
                               | Q(description__icontains=search) | Q(amenities__amenity_name__contains=search))
        

    if sort_by:

        if sort_by == 'low_to_high':
            hotels = hotels.order_by('hotel_price')

        elif sort_by == 'high_to_low':
            hotels = hotels.order_by('-hotel_price')
    if price:

        hotels = hotels.filter(hotel_price__lte=int(price))

    if startdate and enddate:

        unbooked_hotels = []
        for i in hotels:
            valid = check_booking(i.uid, i.room_count, startdate, enddate)
            if valid:
                unbooked_hotels.append(i)
        hotels = unbooked_hotels
    hotels = hotels.distinct ()
    p = Paginator(hotels, 2)
    page_no = request.GET.get('page')

    hotels = p.get_page(1)

    if page_no:
        hotels = p.get_page(page_no)
    no_of_pages = list(range(1, p.num_pages+1))

    date = datetime.today().strftime('%Y-%m-%d')

    context = {'amenities': amenities, 'hotels': hotels, 'sort_by': sort_by,
               'search': search, 'selected_amenities': selected_amenities, 'no_of_pages': no_of_pages, 'max_price': price, 'startdate': startdate, "enddate": enddate, "date": date,'total_hotels':total_hotels}
    return render(request, 'home/index.html', context)


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_obj = authenticate(request, username=username, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, 'Sigin Successfull')
            return redirect('/')
        else:
            messages.error(request, 'Please Enter Valid Name Or Password.')
            return redirect('/')

    return render(request, 'home/signin.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        user = User.objects.filter(username=username)
        if not user.exists():
            user = User.objects.create(
                username=username, password=password, email=email)
            user.save()
            messages.success(request, 'Welcome , Sigup Successfull')
            return render(request, 'home/signin.html')
        else:
            messages.error(
                request, 'Username Or Email Already Exist Please Enter Diffrent Values.')
            redirect('signin')
    return render(request, 'home/signup.html')


def signout(request):
    logout(request)
    return redirect('/')


def get_hotel(request, uid):
    hotel = Hotel.objects.get(uid=uid)
    context = {'hotel': hotel}
    context['date'] = datetime.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        checkin = request.POST.get('startDate')
        checkout = request.POST.get('endDate')
        context['startdate'] = checkin
        context['enddate'] = checkout

        try:
            valid = check_booking(
                hotel.uid, hotel.room_count, checkin, checkout)
            if not valid:
                messages.error(request, 'Booking for these days are full')
                return render(request, 'home/hotel.html', context)
        except:
            messages.error(request, 'Please Enter Valid Date Data')
            return render(request, 'home/hotel.html', context)
        HotelBooking.objects.create(hotel=hotel, user=request.user, start_date=checkin,
                                    end_date=checkout, booking_type='Pre Paid')
        messages.success(
            request, f'{hotel.hotel_name} Booked successfully your booking id is {HotelBooking.uid}.')
        return render(request, 'home/hotel.html', context)
    return render(request, 'home/hotel.html', context)
