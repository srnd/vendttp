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
        public int id;
        public int vendId;
        public int quantity;
        public decimal price;
        public string name;

        public Item(int id, int vendId, decimal price, int quantity, string name)
        {
            this.id = id;
            this.vendId = vendId;
            this.price = price;
            this.quantity = quantity;
            this.name = name;
        }
    }
}
