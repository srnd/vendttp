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
    public class Category
    {
        public List<Item> items;
        string name;

        public Category(string name)
        {
            this.items = new List<Item>();
            this.name = name;
        }

        public Category(string name, List<Item> items)
        {
            this.items = items;
            this.name = name;
        }

        public void addItem(Item item)
        {
            items.Add(item);
        }
    }
}
