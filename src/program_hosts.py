from colorama import Fore
from infrastructure.switchlang import switch
import infrastructure.state as state
import services.data_service as svc
from dateutil import parser
import datetime


def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('a', log_into_account)
            s.case('l', list_cages)
            s.case('r', register_cage)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('Login to your [a]ccount')
    print('[L]ist your cages')
    print('[R]egister a cage')
    print('[U]pdate cage availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')
    
    name = input("What is your name?\n")
    email = input("What is your email?\n").strip().lower()

    old_account = svc.find_account_by_email(email)
    if old_account:
        error_msg(f"ERROR account with email {email} already exists")
        return

    state.active_account = svc.create_account(name, email)
    success_msg(f"Created new account with id {state.active_account.id}")


def log_into_account():
    print(' ****************** LOGIN **************** ')

    email = input("What is your email?\n").strip().lower()
    account = svc.find_account_by_email(email=email)

    if not account:
        error_msg(f"Could not found account with email {email}")
        return

    state.active_account = account
    success_msg("Logged in successfully")


def register_cage():
    print(' ****************** REGISTER CAGE **************** ')

    if not state.active_account:
        error_msg("You must be logged in to register cage")
        return

    meters = input("How many square meters is the cage?\n")
    if not meters:
        error_msg("Cancelled")
        return 

    meters = float(meters)
    carpeted = input("Is the cage carpetted?[y/n]\n").lower().startswith('y')
    has_toys = input("Does the cage have toys?[y/n]\n").lower().startswith('y')
    allow_dangerous = input("Can you host dangerous snakes?[y/n]\n").lower().startswith('y')
    name = input("Give your cage a name\n")
    price = float(input("Renting price for cage\n"))

    cage =svc.register_cage(
        state.active_account,
        name,
        allow_dangerous,
        has_toys,
        carpeted,
        meters,
        price
    )
    state.reload_account()
    success_msg(f"Cage created with id {cage.id}")


def list_cages(supress_header=False):
    if not supress_header:
        print(' ******************     Your cages     **************** ')

    if not state.active_account:
        error_msg("You must be logged in to register cage")
        return

    cages = svc.find_cages_for_account(state.active_account)

    print(f"You have {len(cages)} cages")
    for idx, c in enumerate(cages):
        print(f" {idx+1}. {c.name} of {c.square_meters} meters ")
        for b in c.bookings:
            print("     * Booking: {}, {} days, booked? {}".format(
                b.check_in_date,
                (b.check_out_date - b.check_in_date).days,
                'YES' if b.booked_date is not None else 'NO'
            ))


def update_availability():
    print(' ****************** Add available date **************** ')

    if not state.active_account:
        error_msg("You must be logged in to register cage")
        return

    list_cages(True)

    cage_number = input("Enter cage number\n")

    if not cage_number.strip():
        error_msg("Cancelled")
        print()
        return

    cage_number = int(cage_number)
    cages = svc.find_cages_for_account(state.active_account)
    selected_cage = cages[cage_number-1]
    success_msg(f"Selected Cage {selected_cage.name}")
    
    start_date = parser.parse(
        input("Enter start date [yyyy-mm-dd] : \n")
    )
    days = int(input("How many days is this block of time?\n"))

    svc.add_available_date(
        selected_cage,
        start_date,
        days
    )

    success_msg(f"Date added to cage {selected_cage.name}")


def view_bookings():
    print(' ****************** Your bookings **************** ')

    if not state.active_account:
        error_msg("You must be logged in to view bookings")
        return

    cages = svc.find_cages_for_account(state.active_account)

    bookings = [
        (c, b)
        for c in cages
        for b in c.bookings
        if b.booked_date is not None
    ]

    print("You have {} bookings".format(len(bookings)))
    for c,b in bookings:
        print(" * Cage {}: booked date : {}, from {} for {}| days".format(
            c.name,
            datetime.date(b.booked_date.year, b.booked_date.month, b.booked_date.day),
            datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
            b.duration_in_days
        ))

def exit_app():
    print()
    print('bye')
    raise KeyboardInterrupt()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()


def unknown_command():
    print("Sorry we didn't understand that command.")


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)
