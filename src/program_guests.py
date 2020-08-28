from infrastructure.switchlang import switch
import program_hosts as hosts
import infrastructure.state as state
import services.data_service as svc
from colorama import Fore
from dateutil import parser
import datetime


def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)
            s.case('l', hosts.log_into_account)

            s.case('a', add_a_snake)
            s.case('y', view_your_snakes)
            s.case('b', book_a_cage)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a cage')
    print('[A]dd a snake')
    print('View [y]our snakes')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_snake():
    print(' ****************** Add a snake **************** ')

    if not state.active_account:
        error_msg("You must login first to add snake")
        return

    name = input("What is your snake's name\n")
    if not name:
        error_msg("Cancelled")
        return
    length = float(input("What is your snake's length\n"))
    species = input("Species?\n")
    is_venomous = input("Is your snake venomous?[y/n]").strip().startswith('y')

    snake = svc.add_snake(state.active_account, name, length, species, is_venomous)
    state.reload_account()
    success_msg(f"Created {snake.name} with id {snake.id}")


def view_your_snakes():
    print(' ****************** Your snakes **************** ')

    if not state.active_account:
        error_msg("You must be logged in to view snakes")
        return
    
    snakes = svc.get_snakes_for_user(state.active_account)
    print(f"You have {len(snakes)} snakes")
    for s in snakes:
        print("  * {} of length {}".format(s.name,s.length))



def book_a_cage():
    print(' ****************** Book a cage **************** ')
    
    if not state.active_account:
        error_msg("You must be logged in to create a booking")
        return

    snakes = svc.get_snakes_for_user(state.active_account)
    if not snakes:
        error_msg("You have not any snake registered. [a]dd a snake?")
        return

    print("Let's start by finding available cages")
    start_date_text = input("Check In date [yyyy-mm-dd]")
    if not start_date_text:
        error_msg("Cancelled")
        return

    checkin = parser.parse(start_date_text)

    checkout = parser.parse(input("Check Out date [yyyy-mm-dd]"))

    if checkin >= checkout:
        error_msg("Checkin must be before checkout")
        return

    print()
    for idx, s in enumerate(snakes):
        print("{}. {} (lenght {}, venomous {}".format(
            idx+1, s.name, s.length, 'yes' if s.is_venomous else 'no'
        ))

    snake = snakes[int(input("Select a snake:\n"))-1]
    cages = svc.get_available_cages(checkin, checkout, snake)

    print(f"There are {len(cages)} cages available")
    for idx, c in enumerate(cages):
        print("  {}. {} with {}m, carpetted: {}, has toys: {}".format(
            idx+1,
            c.name,
            c.square_meters,
            "yes" if c.is_carpetted else "no",
            "yes" if c.has_toys else "no"
        ))
    if not cages:
        print("No cages are available")
        return

    cage = cages[int(input("Select a cage:\n"))-1]
    svc.book_cage(state.active_account, snake, cage, checkin, checkout)

    success_msg("Successfully booked cage {} for snake {} at ${}/night".format(
        cage.name, snake.name, cage.price
    ))


def view_bookings():
    print(' ****************** Your bookings **************** ')

    if not state.active_account:
        error_msg("You must be logged in to view bookings")
        return

    snakes = {s.id: s for s in svc.get_snakes_for_user(state.active_account)}
    bookings = svc.get_bookings_for_user(state.active_account)

    print("You have {} bookings".format(len(bookings)))

    for b in bookings:
        print("  * Snake: {} is booked at {} from {} for {} days".format(
            snakes.get(b.guest_snake_id).name,
            b.cage_name,
            datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
            (b.check_out_date - b.check_in_date).days
        ))


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)