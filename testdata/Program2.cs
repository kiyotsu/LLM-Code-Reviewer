using System;
using System.IO;
using System.Text;

namespace B004
{
    class Program
    {
        static void main(string[] args)
        {   

            //テキストファイルの読み込み、リストの宣言
                StreamReader sr = new StreamReader("test6.txt");
            List<string> list = new List<string>();
            string inputIp = sr.ReadLine();
            int number = int.Parse(sr.ReadLine());

            //テキストファイルの内容を１行ごとにリストへ追加
            while(sr.Peek() != -1)
            {
                list.Add(sr.ReadLine());
            }

            //リストに格納した文字列を編集
            string[,] data = new string[number,3];
            int i = 0;
            foreach(string s in list)
            {
                int num = s.IndexOf("-");
                string str1 = list[i].Substring(0,num-1);

                int n1 = s.IndexOf("[");
                int n2 = s.IndexOf("+");
                string str2 = list[i].Substring(n1+1,n2-n1-2);

                int n3 = s.IndexOf("GET");
                int n4 = s.IndexOf("html");
                string str3 = list[i].Substring(n3+4,n4-n3);

                data[i,0] = str1;
                data[i,1] = str2;
                data[i,2] = str3;
                i++;
            }

            Console.WriteLine(inputIp);
            Console.WriteLine(number);


            string[] splitInputIp = inputIp.Split('.');

            for(int p=0;p<data.GetLength(0);p++)
            {
                string[] splitCheckIp = data[p,0].Split('.');
                while(true)
                {
                    //第一オクテットの正誤判定
                    if(splitInputIp[0]!=splitCheckIp[0]) break;

                    //第二オクテットの正誤判定
                    if(splitInputIp[1]!=splitCheckIp[1]) break;
                    //第三オクテットの正誤判定(値が[数値-数値]のような形式の場合には範囲指定を行う)
                    if(splitInputIp[2]!=splitCheckIp[2]&&splitInputIp[2]!="*"&&!splitInputIp[2].Contains("-"))
                    {
                        break;
                    }
                    if(splitInputIp[2].Contains("-")){
                        int x =splitInputIp[2].IndexOf("[");
                        int y =splitInputIp[2].IndexOf("]");
                        string splitIpNumber = splitInputIp[2].Substring(x+1,y-x-1);
                        string[] splitNumber = splitIpNumber.Split('-');
                        
                        if(int.Parse(splitNumber[0])>int.Parse(splitCheckIp[2])||int.Parse(splitNumber[1])<int.Parse(splitCheckIp[2]))
                        {
                            break;
                        }
                    }

                    if(splitInputIp[3]!=splitCheckIp[3]&&splitInputIp[3]!="*")
                    {
                        break;
                    }
                    if(splitInputIp[3].Contains("-")){
                        int x =splitInputIp[3].IndexOf("[");
                        int y =splitInputIp[3].IndexOf("]");
                        string splitIpNumber = splitInputIp[3].Substring(x+1,y-x-1);
                        string[] splitNumber = splitIpNumber.Split('-');
                        if(int.Parse(splitNumber[0])>int.Parse(splitCheckIp[3])||int.Parse(splitNumber[1])<int.Parse(splitCheckIp[3]))
                        {
                            break;
                        }
                    }

                    Console.WriteLine("{0} {1} {2}",data[p,0],data[p,1],data[p,2]);
                    break;
                }
                
                
            }

            
            sr.Close();
        }
    }
}