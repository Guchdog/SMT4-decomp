using u8 = unsigned char;
using u16 = unsigned short;
using u32 = unsigned int;
using s32 = int;
using f32 = float;

struct PlayerActorVisualNode {
    u8 pad_00[0x1f6];
    u8 visible_1f6;
};

struct PlayerActorModelBackend {
    u8 pad_00[0x2c];
    PlayerActorVisualNode* visual_node;
};

struct PlayerActorModel {
    u32 flags;
    u8 pad_04[4];
    PlayerActorModelBackend* backend;
};

struct PlayerActorTransformState {
    u8 active;
    u8 pad_01[3];
    f32 pos[3];
    f32 yaw;
    u32 scale;
    u8 dirty_flag;
    u8 pad_19[3];
    PlayerActorModel* model;
};

struct PlayerActorWork {
    u8 pad_00[0x10];
    PlayerActorTransformState transform;
};

struct RepeatGateWork {
    u8 pad_00[0x22];
    u8 menu_pause_flag;
};

extern "C" {
    extern PlayerActorWork* g_PlayerActorWork_0044cda0;
    extern RepeatGateWork g_RepeatGate_0049f91c;

    void Model_SetTranslation_0028c8a8(PlayerActorModelBackend* backend, u32 mode, const f32* pos);
    void Model_SetRotation_0028c880(PlayerActorModelBackend* backend, u32 mode, f32 pitch, f32 yaw, f32 roll);
    void Model_SetScale_002a5a54(PlayerActorModelBackend* backend, u32 scale, f32 unused);
    void Model_CommitTransform_00287300(PlayerActorModelBackend* backend, u32 scale, f32 unused);

    void h4_player_transform_candidate();
    void h4_player_transform_mutation();
}

void h4_player_transform_candidate() {
    PlayerActorWork* work = g_PlayerActorWork_0044cda0;
    if (!work) return;

    PlayerActorTransformState* state = &work->transform;
    PlayerActorModel* model = state->model;
    if (!model) return;

    PlayerActorModelBackend* backend = model->backend;
    u32 flags = model->flags;

    if (g_RepeatGate_0049f91c.menu_pause_flag) {
        if (!(flags & 2)) {
            model->flags = flags | 2;
            backend->visual_node->visible_1f6 = 0;
        }
        return;
    }

    if (state->active) {
        if (flags & 2) {
            model->flags = flags & ~2;
            backend->visual_node->visible_1f6 = 1;
        }
    } else if (!(flags & 2)) {
        model->flags = flags | 2;
        backend->visual_node->visible_1f6 = 0;
    }

    if (state->dirty_flag) {
        u32 scale = state->scale;
        Model_SetTranslation_0028c8a8(backend, 0, state->pos);
        Model_SetRotation_0028c880(backend, 0, 0.0f, state->yaw, 0.0f);
        Model_SetScale_002a5a54(backend, scale, 0.0f);
        Model_CommitTransform_00287300(backend, scale, 0.0f);
        state->dirty_flag = 0;
    }
}

void h4_player_transform_mutation() {
    PlayerActorWork* work = g_PlayerActorWork_0044cda0;
    if (!work) return;

    PlayerActorTransformState* state = &work->transform;
    PlayerActorModel* model = state->model;
    if (!model) return;

    PlayerActorModelBackend* backend = model->backend;
    u32 flags = model->flags;

    if (g_RepeatGate_0049f91c.menu_pause_flag) {
        if (!(flags & 2)) {
            model->flags = flags | 2;
            backend->visual_node->visible_1f6 = 0;
        }
        return;
    }

    // Inverted active logic
    if (!state->active) {
        if (flags & 2) {
            model->flags = flags & ~2;
            backend->visual_node->visible_1f6 = 1;
        }
    } else if (!(flags & 2)) {
        model->flags = flags | 2;
        backend->visual_node->visible_1f6 = 0;
    }

    if (state->dirty_flag) {
        u32 scale = state->scale;
        Model_SetTranslation_0028c8a8(backend, 0, state->pos);
        Model_SetRotation_0028c880(backend, 0, 0.0f, state->yaw, 0.0f);
        Model_SetScale_002a5a54(backend, scale, 0.0f);
        Model_CommitTransform_00287300(backend, scale, 0.0f);
        state->dirty_flag = 0;
    }
}
