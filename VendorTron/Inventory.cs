using System;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Ink;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Collections.Generic;

namespace VendorTron
{
    public class Inventory
    {
        public List<Category> categories { get; set; }
        public Dictionary<String, Item> IndexDict;

        public Inventory()
        {
            this.categories = new List<Category>();
        }

        public Inventory(List<Category> categories)
        {
            this.categories = categories;
        }
        public Inventory(Category[] categories)
        {
            this.categories = new List<Category>(categories);
        }

        public void add(Category category)
        {
            categories.Add(category);
        }

        public Boolean Index()
        {
            if (categories != null)
            {
                IndexDict = new Dictionary<string, Item>();
                foreach (Category category in categories)
                {
                    foreach (Item item in category.items)
                    {
                        IndexDict[item.vendId] = item;
                    }
                }
                return true;
            }
            else return false;
        }

        public Item FindItem(String vendId)
        {
            if (IndexDict != null)
            {
                try { return IndexDict[vendId]; }
                catch (KeyNotFoundException) { return null; }
            }
            else return null;
        }
    }
}
