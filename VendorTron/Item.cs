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

namespace Vendortron
{
    public class Item
    {
        public int vendId;
        public int quantity;
        public decimal price;
        public String name { get; set; }
        public String sprice { get; set; }
        public String squantity { get; set; }

        public Item(int vendId, decimal price, int quantity, String name)
        {
            this.vendId = vendId;
            this.price = price;
            this.quantity = quantity;
            this.name = name;
            this.sprice = price.ToString("C2");
            this.squantity = quantity.ToString() + " remaining";
        }
    }
}
