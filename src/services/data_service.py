
from data.owners import Owner
from data.cages import Cage
from data.bookings import Booking
from data.snakes import Snake

from typing import List

import datetime

def create_account(name:str, email:str) -> Owner:
    owner = Owner()
    owner.name  = name
    owner.email = email
    owner.save()
    return owner


def find_account_by_email(email: str) -> Owner:
    owner = Owner.objects(email=email).first()
    return owner

def register_cage(account: Owner, name, allow_dangerous,
                  has_toys, carpetted, meters, price) -> Cage:
    cage = Cage()

    cage.name = name
    cage.allow_dangerous_snakes = allow_dangerous
    cage.has_toys = has_toys
    cage.is_carpeted = carpetted
    cage.square_meters = meters
    cage.price = price

    cage.save()

    account = find_account_by_email(account.email)
    account.cage_ids.append(cage.id)
    account.save()

    return cage

def find_cages_for_account(account: Owner) -> List[Cage]:
    query = Cage.objects(id__in=account.cage_ids)
    cages = list(query)
    return cages

def add_available_date(cage: Cage, start_date: datetime.datetime, days: int) -> Cage:

    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)

    cage = Cage.objects(id=cage.id).first()
    cage.bookings.append(booking)
    cage.save()

    return cage

def add_snake(account, name, lenght, species, is_venomous) -> Snake:
    
    snake = Snake()
    snake.name = name
    snake.length = lenght
    snake.is_venomous = is_venomous
    snake.species = species
    snake.save()

    owner = find_account_by_email(account.email)
    owner.snake_ids.append(snake.id)
    owner.save()

    return snake

def get_snakes_for_user(account):
    owner = Owner.objects(id=account.id).first()
    snakes = Snake.objects(id__in=owner.snake_ids).all()
    return list(snakes)

def get_available_cages(checkin, checkout, snake):
    
    min_size = snake.length / 4

    query = Cage.objects() \
        .filter(square_meters__gte=min_size) \
        .filter(bookings__check_in_date__lte=checkin) \
        .filter(bookings__check_out_date__gte=checkout)

    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)

    cages = query.order_by('price', '-square_meters')

    print("Cages", cages)

    final_cages = []
    for c in cages:
        for b in c.bookings:
            if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id == None:
                final_cages.append(c)

    return final_cages

def book_cage(account, snake, cage, checkin, checkout):
    booking = None
    for b in cage.bookings:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id == None:
                booking = b
                break        

    booking.guest_snake_id = snake.id
    booking.guest_owner_id = account.id
    booking.booked_date = datetime.datetime.now()

    cage.save()

def get_bookings_for_user(account):
    account = find_account_by_email(account.email)

    booked_cages = Cage.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')

    def map_cage_to_booking(cage, booking):
        booking.cage = cage
        return booking

    bookings = [
        map_cage_to_booking(cage, booking)
        for cage in booked_cages
        for booking in cage.bookings
        if booking.guest_owner_id = account.id
    ]

    return bookings