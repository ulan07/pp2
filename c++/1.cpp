#include <iostream>
#include <string>
#include <vector>
// #include <conio.h>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <map>
#include <cctype>
#include <sstream>  
#include <iomanip>
#include <set>
#include <queue>
#include <stack> 
#include <utility>
#include <deque>
#include <memory>
 
using namespace std;

unique_ptr<int[]> createNumber(int n){
    unique_ptr<int[]> arr(new int[n]);
    return arr;
}

int main(){
    int n;
    cin>>n;
    auto s=createNumber(n);
    for(int i=0;i<n;i++){
        s[i]=i;
    }
    
    
}