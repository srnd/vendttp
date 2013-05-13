using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MatrixBillAcceptor
{
    internal class HostDataFrame
    {
        public bool StackControl = false;
        public bool ReturnControl = false;
        public bool[] ChannelsEnabled = new bool[] { false, false, false, false, false, false, false, false, false, false, false, false, false, false, false };
        public byte sequenceNumber = 0;

        public static implicit operator byte[](HostDataFrame h)
        {
            Bitmask b = new Bitmask();
            b.Add(0x00);
            b.Add(false, false);
            b.Add(h.StackControl);
            b.Add(h.ReturnControl);
            b.Add(false, false, false, false);
            for (int i = 7; i < 14; i++)
            {
                if (h.ChannelsEnabled.Length < i + 1)
                {
                    b.Add(false);
                }
                else
                {
                    b.Add(h.ChannelsEnabled[i]);
                }
            }
            b.Add(false);
            for (int i = 0; i < 7; i++)
            {
                if (h.ChannelsEnabled.Length < i + 1)
                {
                    b.Add(false);
                }
                else
                {
                    b.Add(h.ChannelsEnabled[i]);
                }
            }
            b.Add(false);
            b.Add(0x00);
            b.Add(h.sequenceNumber);

            return b;
        }
    }
}
