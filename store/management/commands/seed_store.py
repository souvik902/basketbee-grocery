from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help = 'Create BasketBee sample categories and products.'
    def handle(self, *args, **options):
        category_data=[('Fruits & Vegetables','🍎'),('Dairy & Eggs','🥛'),('Rice & Flour','🌾'),('Oil & Masala','🫙'),('Snacks','🍿'),('Beverages','🥤'),('Bakery','🥖'),('Personal Care','🧴'),('Household','🧹'),('Frozen Food','🧊'),('Baby Care','🧸')]
        cats={name:Category.objects.get_or_create(name=name,defaults={'icon':icon})[0] for name,icon in category_data}
        data=[('Basmati Rice','Rice & Flour','India Gate','1 kg',260,225),('Aashirvaad Atta','Rice & Flour','Aashirvaad','5 kg',310,285),('Fortune Sunflower Oil','Oil & Masala','Fortune','1 L',170,155),('Amul Milk','Dairy & Eggs','Amul','1 L',66,None),('Amul Butter','Dairy & Eggs','Amul','100 g',62,55),('Fresh Apples','Fruits & Vegetables','Orchard Fresh','1 kg',210,185),('Fresh Bananas','Fruits & Vegetables','Farm Fresh','1 dozen',60,50),('Fresh Tomatoes','Fruits & Vegetables','Farm Fresh','500 g',35,28),('Fresh Potatoes','Fruits & Vegetables','Farm Fresh','1 kg',45,None),("Lay's Chips",'Snacks',"Lay's",'52 g',25,20),('Maggi','Snacks','Nestle','280 g',70,60),('Coca Cola','Beverages','Coca Cola','750 ml',45,None),('Bread','Bakery','Daily Bake','400 g',48,42),('Eggs','Dairy & Eggs','Happy Hen','6 pcs',78,70),('Sugar','Rice & Flour','Madhur','1 kg',55,None),('Salt','Oil & Masala','Tata','1 kg',25,None),('Tea','Beverages','Tata Tea','250 g',145,130),('Coffee','Beverages','Nescafe','100 g',210,190),('Biscuits','Snacks','Parle','800 g',95,82),('Detergent','Household','Surf Excel','1 kg',180,160)]
        for name,cat,brand,unit,price,discount in data:
            Product.objects.update_or_create(name=name,defaults={'category':cats[cat],'brand':brand,'unit':unit,'price':price,'discount_price':discount,'stock':30,'description':f'A dependable {name.lower()} for your everyday kitchen and home needs.','rating':4.2})
        self.stdout.write(self.style.SUCCESS('Sample store catalog is ready.'))
