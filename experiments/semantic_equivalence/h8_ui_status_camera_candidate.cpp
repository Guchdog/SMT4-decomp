#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef float f32;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void  engine_func_002bc828(u32 a, u32 b, u32 c);
    void  engine_func_002c2210(void* obj, u32 flag);
    void  engine_func_002c20a8(void* obj, const f32* eye, const f32* target, const f32* up);
    void  engine_func_002c1ffc(void* obj, u32 flag, const f32* params);
    void  engine_func_00298fec(void* obj);
    void  engine_func_002c1740(void* obj);
    void  engine_func_002c1774(void* obj, f32 a, f32 b);

    extern void* g_StatusCameraWork_0044e178;
}

struct Vec3 {
    f32 x, y, z;
};

extern "C" void h8_ui_status_camera_candidate(const Vec3* pos, const Vec3* target, const Vec3* up,
                                             f32 fov, f32 aspect, f32 near_p, f32 far_p, f32 extra) {
    u8* work = static_cast<u8*>(g_StatusCameraWork_0044e178);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x53C, 1));
        g_StatusCameraWork_0044e178 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x53C);

    Vec3* work_target = reinterpret_cast<Vec3*>(work + 0x514);
    Vec3* work_pos    = reinterpret_cast<Vec3*>(work + 0x508);
    Vec3* work_up     = reinterpret_cast<Vec3*>(work + 0x520);

    *work_target = *target;
    *work_pos    = *pos;
    *work_up     = *up;

    *reinterpret_cast<f32*>(work + 0x530) = near_p;
    *reinterpret_cast<f32*>(work + 0x534) = fov;
    *reinterpret_cast<f32*>(work + 0x538) = aspect;
    *reinterpret_cast<f32*>(work + 0x52C) = far_p;

    Vec3 view_target;
    view_target.x = work_pos->x + work_target->x * far_p;
    view_target.y = work_pos->y + work_target->y * far_p;
    view_target.z = work_pos->z + work_target->z * far_p;

    f32 up_arr[3];
    up_arr[0] = 0.0f;
    up_arr[1] = 1.0f;
    up_arr[2] = 0.0f;

    engine_func_002bc828(0, 0xC8, 0xF0);
    engine_func_002c2210(work, 1);
    engine_func_002c20a8(work, reinterpret_cast<const f32*>(work_pos), reinterpret_cast<const f32*>(&view_target), up_arr);
    engine_func_002c1ffc(work, 1, reinterpret_cast<const f32*>(work + 0x530));
    engine_func_00298fec(work);
    engine_func_002c1740(work);
    engine_func_002c1774(work, extra, far_p);
}

extern "C" void h8_ui_status_camera_mutation(const Vec3* pos, const Vec3* target, const Vec3* up,
                                             f32 fov, f32 aspect, f32 near_p, f32 far_p, f32 extra) {
    g_StatusCameraWork_0044e178 = nullptr;
}
