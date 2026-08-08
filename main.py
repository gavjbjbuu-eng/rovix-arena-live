import random
import os

# Load User Balance
if os.path.exists("balance.txt"):
    with open("balance.txt", "r") as f:
        try:
            balance = int(f.read().strip())
        except ValueError:
            balance = 1000
else:
    balance = 1000

# Load Admin Wallet
if os.path.exists("admin_wallet.txt"):
    with open("admin_wallet.txt", "r") as f:
        try:
            admin_wallet = int(f.read().strip())
            if admin_wallet < 0:
                admin_wallet = 20000
        except ValueError:
            admin_wallet = 20000
else:
    admin_wallet = 20000

# Load Total Bets Track
if os.path.exists("total_bets.txt"):
    with open("total_bets.txt", "r") as f:
        try:
            total_bets_count = int(f.read().strip())
        except ValueError:
            total_bets_count = 0
else:
    total_bets_count = 0

consecutive_wins = 0

def play_rovix_greedy(user_currency, admin_bal, total_bets):
    global consecutive_wins
    
    print("\n--------------------------------")
    print(f"💰 Current Cheers: {user_currency}")
    print("1. Play Game (Spin Wheel)")
    print("2. Recharge Cheers (Buy Packs)")
    print("3. Gift Cheers to Creator")
    print("4. Check Creator Earnings")
    print("5. Admin Dashboard")
    print("0. Exit")
    
    choice =  "0"  "0" # input("Choose an option: ").strip()
    
    if choice == '0':
        return -1, user_currency, admin_bal, total_bets
        
    elif choice == '5':
        print("\n--- 🔐 ADMIN DASHBOARD (NO LOSS SYSTEM) ---")
        print(f"💼 Admin Wallet Balance: {admin_bal} Cheers")
        print(f"📊 Total Bets Placed Count: {total_bets}")
        if os.path.exists("creator_earnings.txt"):
            with open("creator_earnings.txt", "r") as f:
                try:
                    total_gifted_cheers = int(f.read().strip())
                except ValueError:
                    total_gifted_cheers = 0
        else:
            total_gifted_cheers = 0
            
        ice_coins = total_gifted_cheers / 4  # 8 cheers = 2 ice coins -> 1 cheers = 0.25 ice coin
        rupees_value = ice_coins / 2        # 2 ice coins = 1 rupee
        print(f"🎁 Total Creator Gifts: {total_gifted_cheers} Cheers")
        print(f"🪙 Equivalent Ice Coins: {ice_coins}")
        print(f"💵 Equivalent Creator Income in Rupees: ₹{rupees_value}")
        return user_currency, admin_bal, total_bets
        
    elif choice == '4':
        if os.path.exists("creator_earnings.txt"):
            with open("creator_earnings.txt", "r") as f:
                total_gifted = f.read().strip()
                print(f"🏆 Total Cheers Received by Creators: {total_gifted} Cheers")
        else:
            print("🏆 Total Cheers Received by Creators: 0 Cheers")
        return user_currency, admin_bal, total_bets
        
    elif choice == '2':
        print("\n--- 💎 RECHARGE CHEERS (PACKS) ---")
        print("1. ₹99   -> 500 Cheers")
        print("2. ₹350  -> 2000 Cheers")
        print("3. ₹800  -> 4000 Cheers")
        print("4. ₹1500 -> 7500 Cheers")
        print("5. ₹3700 -> 18000 Cheers")
        print("6. ₹11000-> 56000 Cheers")
        print("7. ₹990000-> 5,00,000 Cheers")
        
        pack_choice =  "0"  "0" # input("Select a pack option (1-7): ").strip()
        
        added_cheers = 0
        if pack_choice == '1': added_cheers = 500
        elif pack_choice == '2': added_cheers = 2000
        elif pack_choice == '3': added_cheers = 4000
        elif pack_choice == '4': added_cheers = 7500
        elif pack_choice == '5': added_cheers = 18000
        elif pack_choice == '6': added_cheers = 56000
        elif pack_choice == '7': added_cheers = 500000
        else:
            print("❌ Invalid pack choice!")
            return user_currency, admin_bal, total_bets
            
        user_currency += added_cheers
        admin_bal += added_cheers  # Recharge money safely goes to admin/system wallet
        print(f"✅ Successfully added {added_cheers} Cheers to your wallet!")
        return user_currency, admin_bal, total_bets
    
    elif choice == '3':
        if user_currency <= 0:
            print("❌ Not enough cheers to gift!")
            return user_currency, admin_bal, total_bets
        
        creator_name =  "0"  "0" # input("Enter Creator Name to gift: ").strip()
        if not creator_name:
            print("❌ Invalid creator name!")
            return user_currency, admin_bal, total_bets
            
        try:
            gift_amt = int( "0"  "0" # input("Enter cheers amount to gift: "))
        except ValueError:
            print("❌ Invalid input!")
            return user_currency, admin_bal, total_bets
            
        if gift_amt > user_currency or gift_amt <= 0:
            print("❌ Invalid gift amount!")
            return user_currency, admin_bal, total_bets
            
        user_currency -= gift_amt
        
        current_creator_total = 0
        if os.path.exists("creator_earnings.txt"):
            with open("creator_earnings.txt", "r") as f:
                try:
                    current_creator_total = int(f.read().strip())
                except ValueError:
                    current_creator_total = 0
                    
        current_creator_total += gift_amt
        with open("creator_earnings.txt", "w") as f:
            f.write(str(current_creator_total))
            
        ice_coins_got = (gift_amt / 8) * 2
        rupees_got = ice_coins_got / 2
        
        print(f"🎁 Successfully gifted {gift_amt} Cheers to {creator_name}! ❤️")
        print(f"🪙 Creator got: {ice_coins_got} Ice Coins (Worth ₹{rupees_got})")
        print(f"💼 Remaining Balance: {user_currency} Cheers")
        return user_currency, admin_bal, total_bets

    elif choice == '1':
        try:
            bet = int( "0"  "0" # input("Enter your bet amount: "))
        except ValueError:
            print("❌ Invalid input! Numbers only.")
            return user_currency, admin_bal, total_bets

        if bet > user_currency or bet <= 0:
            print("❌ Not enough cheers or invalid bet!")
            return user_currency, admin_bal, total_bets

        total_bets += 1
        user_currency -= bet  
        admin_bal += bet      # Bet securely enters admin pool

        # Anti-streak safety to protect admin from continuous wins
        if consecutive_wins >= 2:
            items_pool = [0, 0, 0, 0, 5] 
            consecutive_wins = 0 
        else:
            items_pool = [0, 0, 5, 5, 5, 5, 10, 15, 25, 75]

        selected_multiplier = random.choice(items_pool)
        
        print("🔄 Spinning the wheel...")
        
        winnings = int(bet * selected_multiplier)
        
        # Absolute Admin Protection: Admin will NEVER go negative or face loss
        if winnings > 0:
            if admin_bal >= winnings:
                admin_bal -= winnings
                user_currency += winnings
            else:
                winnings = max(0, admin_bal)
                admin_bal = 0
                user_currency += winnings
                print("🛡️ House Protection Active: Payout capped safely to protect Admin!")

        if winnings > bet:
            consecutive_wins += 1
        else:
            consecutive_wins = 0
        
        print(f"🎯 Wheel stopped at: {selected_multiplier}x Multiplier!")
        print(f"✨ You won: {winnings} Cheers!")
        print(f"💼 Updated Wallet Balance: {user_currency} Cheers")
        
        return user_currency, admin_bal, total_bets
    else:
        print("❌ Invalid choice!")
        return user_currency, admin_bal, total_bets

while balance > 0:
    balance, admin_wallet, total_bets_count = play_rovix_greedy(balance, admin_wallet, total_bets_count)
    
    if balance == -1:
        print("👋 Exiting ROVIX game. All data saved!")
        break
        
    with open("balance.txt", "w") as f:
        f.write(str(balance))
        
    with open("admin_wallet.txt", "w") as f:
        f.write(str(admin_wallet))
        
    with open("total_bets.txt", "w") as f:
        f.write(str(total_bets_count))
        
    cont =  "0"  "0" # input("\nContinue app? (y/n): ").strip().lower()
    if cont != 'y':
        print("👋 Game saved! See you soon.")
        break

