import sys, os
sys.path.insert(0, '/workspaces/cap-lang')

import time
print('=== Complex CapLang Demo ===')
print('(pyspigot import omitted for compiled demo)')
sum = 0.0
even = False
i = 1.0
while (i <= 10.0):
    ((not even)); even = ((not even)); even
    print(i)
    if even:
        print('even')
    else:
        print('odd')
    (sum + i); sum = (sum + i); sum
    (i + 1.0); i = (i + 1.0); i
print('Sum 1..10:')
print(sum)
n = 6.0
fact = 1.0
while (n > 1.0):
    (fact * n); fact = (fact * n); fact
    (n - 1.0); n = (n - 1.0); n
print('6! =')
print(fact)
greeting = 'Inside block'
print(greeting)
print('block done')
print('Demo complete')
if True:
    print("--- interactive demo (won't run in automated test) ---")
    name = input('Your name: ')
    print(('Hello, ' + name))
    time.sleep(2.0)
    print('(slept 2s)')
