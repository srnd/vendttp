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
using System.Xml.Linq;

namespace Vendortron
{
    public class Item
    {
        public String vendId { get; private set; }
        public int quantity { get; private set; }
        public decimal price { get; private set; }
        public String name { get; private set; }
        public String info { get; private set; }

        public Item(String vendId, decimal price, int quantity, String name)
        {
            this.vendId = vendId;
            this.price = price;
            this.quantity = quantity;
            this.name = name;
            this.UpdateInfo();
        }

        private void UpdateInfo()
        {
            if (this.quantity > 0)
            {
                this.info = this.price.ToString("C2");
            }
            else
            {
                this.info = "SOLD OUT";
            }
        }

        public static Item ParseXElement(XElement element)
        {
            return new Item(element.Attribute("vendId").Value,
                            decimal.Parse(element.Attribute("price").Value),
                            int.Parse(element.Attribute("quantity").Value),
                            element.Attribute("name").Value);
        }

        public void decrement()
        {
            this.quantity--;
            this.UpdateInfo();
        }
    }
}
