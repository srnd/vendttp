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

namespace Vendortron
{
    public class Inventory
    {
        public List<Category> categories;

        public Inventory()
        {
            this.categories = new List<Category>();
        }

        public Inventory(List<Category> categories)
        {
            this.categories = categories;
        }

        public void add(Category category)
        {
            categories.Add(category);
        }

        public void add(string name, List<Item> items)
        {
            categories.Add(new Category(name, items));
        }
    }
}
